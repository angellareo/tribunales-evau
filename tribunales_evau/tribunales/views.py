import logging
from math import ceil

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from openpyxl import Workbook
from openpyxl.styles import Font
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value
from pulp.apis import PULP_CBC_CMD
from tribunales.models import Asignatura, Evaluador, Examen, Sede

logger = logging.getLogger(__name__)

# CACHE_PREFIX = "moves_"

weekday_names_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def get_moves(asignatura):
    move_data = cache.get(str(asignatura))

    if move_data is not None:
        return move_data

    logger.debug("Recalculating moves for " + str(asignatura))
    sedes = Sede.objects.all()

    headquarter_data = {}
    fechas = set()
    for sede in sedes:
        sede_id = sede.COD_SEDE
        examenes = Examen.objects.filter(COD_SEDE=sede_id, COD_ASIGNATURA=asignatura)
        for examen in examenes:
            fecha = examen.FECHA
            fechas.add(fecha)
            if str(sede_id) + "_" + str(fecha) not in headquarter_data:
                headquarter_data[str(sede_id) + "_" + str(fecha)] = {"exams": 0, "evals": 0}
            headquarter_data[str(sede_id) + "_" + str(fecha)]["exams"] += examen.EXAMENES

    for sede in sedes:
        sede_id = sede.COD_SEDE
        try:
            evaluadores = Evaluador.objects.get(COD_SEDE=sede_id, COD_ASIGNATURA=asignatura)
            evals = evaluadores.EVALUADORES
            for fecha in fechas:
                if str(sede_id) + "_" + str(fecha) not in headquarter_data:
                    headquarter_data[str(sede_id) + "_" + str(fecha)] = {"exams": 0, "evals": 0}
                headquarter_data[str(sede_id) + "_" + str(fecha)]["evals"] += evals
        except ObjectDoesNotExist:
            evals = 0
    logger.debug("hq_data: " + str(headquarter_data))

    if sum(data["evals"] for data in headquarter_data.values()) == 0:
        logger.debug("No data in DB")
        return {"mean": None, "total_moves": None, "move_details": None}

    # Calculate mean
    mean = ceil(
        sum(data["exams"] for data in headquarter_data.values())
        / sum(data["evals"] for data in headquarter_data.values())
    )

    # Create a LP problem
    prob = LpProblem("Headquarters_Movement", LpMinimize)

    # Decision variables
    HQs = list(headquarter_data.keys())
    HQs_from = []
    HQs_to = []
    for HQ in HQs:
        if mean * headquarter_data[HQ]["evals"] > headquarter_data[HQ]["exams"]:
            HQs_to.append(HQ)
        else:
            HQs_from.append(HQ)

    num_exchanges = LpVariable("num_exchanges", lowBound=0, cat="Integer")  # The number of exchanges

    moves = LpVariable.dicts("moves", (HQs_from, HQs_to), lowBound=0, cat="Integer")
    exchanges = LpVariable.dicts("exchange", ((i, j) for i in HQs_from for j in HQs_to), cat="Binary")

    # Constraints
    for i in HQs_from:
        for j in HQs_to:
            prob += moves[i][j] >= 0
            prob += (
                moves[i][j] <= headquarter_data[i]["exams"] * exchanges[i, j]
            )  # No movements allowed if exchange[i][j] = 0
            prob += moves[i][j] <= max(
                0,
                min(
                    (headquarter_data[i]["exams"] - (mean * headquarter_data[i]["evals"])),
                    max((mean * headquarter_data[j]["evals"]) - headquarter_data[j]["exams"], 0),
                ),
            )

    for i in HQs_from:
        prob += lpSum(moves[i][j] for j in HQs_to) <= max(
            headquarter_data[i]["exams"] - (mean * headquarter_data[i]["evals"]), 0
        )

    for j in HQs_to:
        prob += (
            lpSum(moves[i][j] for i in HQs_from)
            >= (mean * headquarter_data[j]["evals"]) - headquarter_data[j]["exams"]
        )

    # Total number of exams moved - not needed
    # prob += num_moves == lpSum(moves[i][j] for i in HQ for j in HQ)

    # Define total number of exchanges
    prob += num_exchanges == lpSum([exchanges[i, j] for i in HQs_from for j in HQs_to])

    # Objective: minimize the number of exchanges
    prob += num_exchanges

    # prob.solve(PULP_CBC_CMD(msg=False, options=['TimeLimit=60']))
    prob.solve(PULP_CBC_CMD(msg=False, mip=True))

    # Output the results
    total_moves = value(prob.objective)
    move_details = {}
    for i in HQs_from:
        for j in HQs_to:
            if value(moves[i][j]) > 0:
                if i not in move_details:
                    move_details[i] = {}
                move_details[i][j] = int(value(moves[i][j]))
    move_data = {"mean": mean, "total_moves": total_moves, "move_details": move_details}

    cache.set(str(asignatura), move_data, timeout=None)
    return cache.get(str(asignatura))


class MovesView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")

    def get(self, request):
        # Logic to get asignaturas
        self.asignaturas = Asignatura.objects.all()

        cod_asignatura = request.GET.get("asignatura")

        # Assuming you have a function to get moves
        if cod_asignatura is not None:
            move_data = get_moves(cod_asignatura)
            move_details = []
            if move_data["move_details"] is not None:
                for from_HQ in move_data["move_details"].keys():
                    from_parts = from_HQ.split("_")
                    from_sede_id = from_parts[0]
                    from_fecha = from_parts[1]
                    for to_HQ in move_data["move_details"][from_HQ].keys():
                        to_parts = to_HQ.split("_")
                        to_sede_id = to_parts[0]
                        to_fecha = to_parts[1]
                        from_sede = Sede.objects.get(COD_SEDE=from_sede_id).UBICACION
                        to_sede = Sede.objects.get(COD_SEDE=to_sede_id).UBICACION
                        n_exams = int(move_data["move_details"][from_HQ][to_HQ])
                        move_details.append(
                            {
                                "from_HQ": from_sede,
                                "from_fecha": from_fecha,
                                "to_HQ": to_sede,
                                "to_fecha": to_fecha,
                                "num_moves": n_exams,
                            }
                        )
            return render(
                request,
                "moves_template.html",
                {
                    "asignaturas": self.asignaturas,
                    "nombre_asignatura": Asignatura.objects.get(COD_ASIGNATURA=cod_asignatura).ASIGNATURA,
                    "mean": move_data["mean"],
                    "total_moves": move_data["total_moves"],
                    "move_details": move_details,
                },
            )
        else:
            return render(request, "moves_template.html", {"asignaturas": self.asignaturas})


class MovesXLSView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")

    moves_data = {}

    def print_header(self, ws, sede):
        sede_title = [" ", "SEDE " + str(sede), " ", " ", "Intercambio de exámenes con otras sedes"]
        ws.append(sede_title)
        row = ws.row_dimensions[1]
        row.font = Font(bold=True)

        ws.merge_cells(start_row=3, start_column=6, end_row=3, end_column=8)
        ws.merge_cells(start_row=3, start_column=9, end_row=3, end_column=11)
        ws["F3"] = "# Exámenes a Enviar"
        ws["I3"] = "# Exámenes a recibir"

        header = [
            " ",
            "ASIGNATURA",
            "Nº Exám/Sede",
            "nº Correctores/sede",
            "MEDIA UAM",
            "Teóricos",
            "Reales",
            "Sede\ndestino",
            "Teóricos",
            "Reales",
            "Sede\norigen",
        ]
        ws.append(header)

    def get(self, request):
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = 'attachment; filename="sede_data.xlsx"'

        wb = Workbook()
        # Remove the default first sheet
        default_sheet = wb.active
        wb.remove(default_sheet)

        # Fetch data from DB
        sedes = Sede.objects.all()

        for sede in sedes:
            # Create a new sheet for each SEDE
            ws = wb.create_sheet(title="SEDE " + str(sede.COD_SEDE))
            self.print_header(ws, sede.COD_SEDE)

            queryset = (
                Examen.objects.filter(COD_SEDE_id=sede.COD_SEDE)
                .select_related("COD_ASIGNATURA")
                .order_by("FECHA", "COD_ASIGNATURA")
            )

            # Write data rows
            for examen in queryset:
                try:
                    evaluadores = Evaluador.objects.get(
                        COD_SEDE=sede.COD_SEDE, COD_ASIGNATURA=examen.COD_ASIGNATURA
                    ).EVALUADORES
                except ObjectDoesNotExist:
                    evaluadores = 0

                # get_moves
                if examen.COD_ASIGNATURA not in self.moves_data:
                    self.moves_data[examen.COD_ASIGNATURA_id] = get_moves(examen.COD_ASIGNATURA_id)
                moves = self.moves_data[examen.COD_ASIGNATURA_id]

                HQ = str(examen.COD_SEDE_id) + "_" + str(examen.FECHA)
                if HQ in moves["move_details"]:
                    for to_HQ in moves["move_details"][HQ].keys():
                        sede_destino = to_HQ.split("_")[0]
                        row_data = [
                            weekday_names_es[examen.FECHA.isoweekday() - 1],
                            examen.COD_ASIGNATURA.ASIGNATURA,
                            examen.EXAMENES,
                            evaluadores,
                            moves["mean"],  # media_uam,
                            moves["move_details"][HQ][to_HQ],  # envio_teoricos,
                            " ",  # envio_reales,
                            sede_destino,  # envio_sede_destino,
                            " ",  # recibido_teoricos,
                            " ",  # recibido_reales,
                            " ",  # asignatura.recibido_sede_origen
                        ]
                        ws.append(row_data)
                else:
                    for from_HQ in moves["move_details"].keys():
                        if HQ in moves["move_details"][from_HQ].keys():
                            sede_origen = from_HQ.split("_")[0]
                            row_data = [
                                weekday_names_es[examen.FECHA.isoweekday() - 1],
                                examen.COD_ASIGNATURA.ASIGNATURA,
                                examen.EXAMENES,
                                evaluadores,
                                moves["mean"],  # media_uam,
                                " ",  # envio_teoricos,
                                " ",  # envio_reales,
                                " ",  # envio_sede_destino,
                                moves["move_details"][from_HQ][HQ],  # recibido_teoricos,
                                " ",  # recibido_reales,
                                sede_origen,  # asignatura.recibido_sede_origen
                            ]
                            ws.append(row_data)
        # Save the workbook to the response
        logger.debug("saving workbook")
        wb.save(response)

        return response
