from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from tribunales.models import Asignatura, Headquarter, Sede


class SedeResource(resources.ModelResource):
    class Meta:
        model = Sede
        import_id_fields = ["COD_SEDE"]


class SedeAdmin(ImportExportModelAdmin):
    resource_classes = [SedeResource]


class AsignaturaResource(resources.ModelResource):
    class Meta:
        model = Asignatura
        import_id_fields = ["COD_ASIGNATURA"]


class AsignaturaAdmin(ImportExportModelAdmin):
    resource_classes = [AsignaturaResource]


class HeadquarterResource(resources.ModelResource):
    class Meta:
        model = Headquarter
        import_id_fields = ["COD_SEDE", "COD_ASIGNATURA"]


class HeadquarterAdmin(ImportExportModelAdmin):
    resource_classes = [HeadquarterResource]


if Sede not in admin.site._registry:
    admin.site.register(Sede, SedeAdmin)
if Asignatura not in admin.site._registry:
    admin.site.register(Asignatura, AsignaturaAdmin)
if Headquarter not in admin.site._registry:
    admin.site.register(Headquarter, HeadquarterAdmin)
