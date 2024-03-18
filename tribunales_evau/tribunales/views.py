import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value
from pulp.apis import PULP_CBC_CMD
from tribunales.models import Asignatura, Headquarter, Sede

logger = logging.getLogger(__name__)


class MovesView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")

    def get_moves(self, asignatura):
        # Retrieve data from Headquarter model
        # headquarters = Headquarter.objects.all()
        headquarters = Headquarter.objects.filter(COD_ASIGNATURA=asignatura)

        # Organize data into a dictionary for easier processing
        headquarter_data = {}
        for headquarter in headquarters:
            sede_id = headquarter.COD_SEDE_id
            if sede_id not in headquarter_data:
                headquarter_data[sede_id] = {"exams": 0, "evals": 0}
            headquarter_data[sede_id]["exams"] += headquarter.EXAMENES
            headquarter_data[sede_id]["evals"] += headquarter.EVALUADORES

        if sum(data["evals"] for data in headquarter_data.values()) == 0:
            logger.info("No data in DB")
            return {"mean": None, "total_moves": None, "move_details": None}

        # Calculate mean
        mean = sum(data["exams"] for data in headquarter_data.values()) // sum(
            data["evals"] for data in headquarter_data.values()
        )

        # Create a LP problem
        prob = LpProblem("Headquarters_Movement", LpMinimize)

        # Decision variables
        HQ = list(headquarter_data.keys())
        # print("HQ: "+str(HQ))

        # num_moves = LpVariable("num_moves", lowBound=0, cat="Integer")  # The number of moves
        num_exchanges = LpVariable("num_exchanges", lowBound=0, cat="Integer")  # The number of exchanges

        moves = LpVariable.dicts("moves", (HQ, HQ), lowBound=0, cat="Integer")
        exchanges = LpVariable.dicts("exchange", ((i, j) for i in HQ for j in HQ), cat="Binary")

        # Constraints
        for i in HQ:
            for j in HQ:
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

        for i in HQ:
            prob += lpSum(moves[i][j] for j in HQ) <= max(
                headquarter_data[i]["exams"] - (mean * headquarter_data[i]["evals"]), 0
            )

        for j in HQ:
            prob += (
                lpSum(moves[i][j] for i in HQ) >= (mean * headquarter_data[j]["evals"]) - headquarter_data[j]["exams"]
            )

        # Total number of exams moved - not needed
        # prob += num_moves == lpSum(moves[i][j] for i in HQ for j in HQ)

        # Define total number of exchanges
        prob += num_exchanges == lpSum([exchanges[i, j] for i in HQ for j in HQ])

        # Objective: minimize the number of exchanges
        prob += num_exchanges

        prob.solve(PULP_CBC_CMD(msg=False))

        # Output the results
        total_moves = value(prob.objective)
        move_details = []
        for i in HQ:
            for j in HQ:
                if value(moves[i][j]) > 0:
                    from_sede = Sede.objects.get(COD_SEDE=i).UBICACION
                    to_sede = Sede.objects.get(COD_SEDE=j).UBICACION
                    move_details.append({"from_HQ": from_sede, "to_HQ": to_sede, "num_moves": int(value(moves[i][j]))})
        return {"mean": mean, "total_moves": total_moves, "move_details": move_details}

    def get(self, request):
        # Logic to get asignaturas
        self.asignaturas = Asignatura.objects.all()

        cod_asignatura = request.GET.get("asignatura")

        # Assuming you have a function to get moves
        if cod_asignatura is not None:
            move_data = self.get_moves(cod_asignatura)

            return render(
                request,
                "moves_template.html",
                {
                    "asignaturas": self.asignaturas,
                    "nombre_asignatura": Asignatura.objects.get(COD_ASIGNATURA=cod_asignatura).ASIGNATURA,
                    "mean": move_data["mean"],
                    "total_moves": move_data["total_moves"],
                    "move_details": move_data["move_details"],
                },
            )
        else:
            return render(request, "moves_template.html", {"asignaturas": self.asignaturas})
