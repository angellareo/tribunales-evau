from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.widgets import DateWidget
from tribunales.models import Asignatura, Evaluador, Examen, Sede


class SedeResource(resources.ModelResource):
    class Meta:
        model = Sede
        import_id_fields = ["COD_SEDE", "UBICACION"]


class SedeAdmin(ImportExportModelAdmin):
    resource_classes = [SedeResource]


class AsignaturaResource(resources.ModelResource):
    class Meta:
        model = Asignatura
        import_id_fields = ["COD_ASIGNATURA", "ASIGNATURA"]


class AsignaturaAdmin(ImportExportModelAdmin):
    resource_classes = [AsignaturaResource]


class EvaluadorResource(resources.ModelResource):
    class Meta:
        model = Evaluador
        import_id_fields = ["COD_SEDE", "COD_ASIGNATURA", "EVALUADORES"]


class EvaluadorAdmin(ImportExportModelAdmin):
    resource_classes = [EvaluadorResource]


class ExamenResource(resources.ModelResource):
    FECHA = Field(attribute="FECHA", column_name="FECHA", widget=DateWidget(format="%d/%m/%y"))

    class Meta:
        model = Examen
        import_id_fields = ["COD_SEDE", "COD_ASIGNATURA", "FECHA", "EXAMENES"]


class ExamenAdmin(ImportExportModelAdmin):
    resource_classes = [ExamenResource]


if Sede not in admin.site._registry:
    admin.site.register(Sede, SedeAdmin)
if Asignatura not in admin.site._registry:
    admin.site.register(Asignatura, AsignaturaAdmin)
if Evaluador not in admin.site._registry:
    admin.site.register(Evaluador, EvaluadorAdmin)
if Examen not in admin.site._registry:
    admin.site.register(Examen, ExamenAdmin)
