import csv
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from .models import Sede, Asignatura, Evaluador


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

@admin.register(Evaluador)
class EvaluadoresAdmin(admin.ModelAdmin, ExportCsvMixin):
    add_form_template = 'admin/evaluadores.html'

    actions = ["export_as_csv"]

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path('add/import-agg-csv/', self.import_agg_csv),
        ]
        return added_urls + urls

    def load_csv_to_db(self, csv_data):
        seen_cod_sedes = set()
        seen_cod_asignaturas = set()
        seen_pairs = set()
        for row in csv_data:
            cod_sede = row['COD_SEDE']
            cod_asignatura = row['COD_ASIGNATURA']
            pair = (cod_sede, cod_asignatura)
            if cod_sede not in seen_cod_sedes:
                seen_cod_sedes.add(cod_sede)
                sede_data = {
                    'COD_SEDE': cod_sede,
                    'UBICACION': row['UBICACION'],
                }
            if cod_asignatura not in seen_cod_asignaturas:
                seen_cod_asignaturas.add(cod_asignatura)
                asignatura_data = {
                    'COD_ASIGNATURA': cod_asignatura,
                    'ASIGNATURA': row['ASIGNATURA'],
                }
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                evaluador_data = {
                    'COD_SEDE_id': row['COD_SEDE'],
                    'COD_ASIGNATURA_id': row['COD_ASIGNATURA'],
                    'TOTAL': row['TOTAL'],
                }
            Sede.objects.create(**sede_data)
            Asignatura.objects.create(**asignatura_data)
            Evaluador.objects.create(**evaluador_data)

    def import_agg_csv(self, request):
        encoding = 'latin-1' # might be 'utf-8'
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            csv_data = csv.DictReader(csv_file.read().decode('latin-1').splitlines())
            self.load_csv_to_db(csv_data)
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "admin/csv_form.html", payload
        )

    import_agg_csv.short_description = "Import Aggregated CSV"

    # def import_csv(modeladmin, request, queryset):
    #     model = queryset.model
    #     csv_file = request.FILES['csv_file']

    #     csv_data = csv.DictReader(csv_file)
    #     for row in csv_data:
    #         model.objects.create(**row)

    # import_csv.short_description = "Import CSV"

admin.site.register(Sede)
admin.site.register(Asignatura)