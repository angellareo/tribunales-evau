import csv

from django import forms
from django.contrib import admin, messages
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path

from .models import Asignatura, Headquarter, Sede


class ExportCsvMixin:
    @admin.action(description="Export Selected")
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(Headquarter)
class HeadquarterAdmin(admin.ModelAdmin, ExportCsvMixin):
    add_form_template = "admin/evaluadores.html"

    actions = ["export_as_csv"]

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path("add/import-agg-csv/", self.import_agg_csv),
        ]
        return added_urls + urls

    def data_to_db(self, request):
        sede_data = request.session.pop("sede_data", None)
        asignatura_data = request.session.pop("asignatura_data", None)
        headquarter_data = request.session.pop("headquarter_data", None)
        for sede_entry in sede_data:
            Sede.objects.create(**sede_entry)
        for asignatura_entry in asignatura_data:
            Asignatura.objects.create(**asignatura_entry)
        for headquarter_entry in headquarter_data:
            Headquarter.objects.create(**headquarter_entry)
        request.session.modified = True  # Set modified to True to save changes

    def is_data_ok(self, request):
        # Check if data is loaded in session
        return (
            "sede_data" in request.session
            and "asignatura_data" in request.session
            and "evaluador_data" in request.session
        )

    def load_csv_data(self, request):
        encoding = "latin-1"  # might be 'utf-8'
        csv_file = request.FILES["csv_file"]
        csv_data = csv.DictReader(csv_file.read().decode(encoding).splitlines())
        seen_cod_sedes = set()
        sede_data = []
        seen_cod_asignaturas = set()
        asignatura_data = []
        seen_pairs = set()
        evaluador_data = []
        for row in csv_data:
            cod_sede = row["COD_SEDE"]
            cod_asignatura = row["COD_ASIGNATURA"]
            pair = (cod_sede, cod_asignatura)
            if cod_sede not in seen_cod_sedes:
                seen_cod_sedes.add(cod_sede)
                sede_data.append(
                    {
                        "COD_SEDE": cod_sede,
                        "UBICACION": row["UBICACION"],
                    }
                )
            if cod_asignatura not in seen_cod_asignaturas:
                seen_cod_asignaturas.add(cod_asignatura)
                asignatura_data.append(
                    {
                        "COD_ASIGNATURA": cod_asignatura,
                        "ASIGNATURA": row["ASIGNATURA"],
                    }
                )
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                evaluador_data.append(
                    {
                        "COD_SEDE_id": row["COD_SEDE"],
                        "COD_ASIGNATURA_id": row["COD_ASIGNATURA"],
                        "TOTAL": row["TOTAL"],
                    }
                )
        request.session["sede_data"] = sede_data
        request.session["asignatura_data"] = asignatura_data
        request.session["evaluador_data"] = evaluador_data

    @admin.display(description="Import Aggregated CSV")
    def import_agg_csv(self, request):
        if not self.is_data_ok(request) and request.method == "POST":
            self.load_csv_data(request)
            self.message_user(request, "Check data and click Import data")
            messages.info(request, f"Sede data: {request.session['sede_data']}")
            messages.info(request, f"Asignatura data: {request.session['asignatura_data']}")
            messages.info(request, f"Headquarter data: {request.session['headquarter_data']}")
            form = CsvImportForm()
            payload = {"form": form}
            return render(request, "admin/csv_form.html", payload)

        if self.is_data_ok(request) and request.method == "POST":
            self.data_to_db(request)
            self.message_user(request, "Your data has been imported to db")
            return redirect("..")

        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_form.html", payload)

    # def import_csv(modeladmin, request, queryset):
    #     model = queryset.model
    #     csv_file = request.FILES['csv_file']

    #     csv_data = csv.DictReader(csv_file)
    #     for row in csv_data:
    #         model.objects.create(**row)

    # import_csv.short_description = "Import CSV"


admin.site.register(Sede)
admin.site.register(Asignatura)
