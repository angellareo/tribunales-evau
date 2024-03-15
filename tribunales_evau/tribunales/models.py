from django.db import models


class Sede(models.Model):
    COD_SEDE = models.AutoField(primary_key=True)
    UBICACION = models.CharField(max_length=100)


class Asignatura(models.Model):
    COD_ASIGNATURA = models.AutoField(primary_key=True)
    ASIGNATURA = models.CharField(max_length=100)


class Headquarter(models.Model):
    COD_SEDE = models.ForeignKey(Sede, on_delete=models.CASCADE)
    COD_ASIGNATURA = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    EVALUADORES = models.IntegerField()
    EXAMENES = models.IntegerField()

    class Meta:
        verbose_name_plural = "Headquarters"
