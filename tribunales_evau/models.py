from django.db import models

class Sedes(models.Model):
    COD_SEDE = models.AutoField(primary_key=True)
    UBICACION = models.CharField(max_length=100)

class Asignaturas(models.Model):
    COD_ASIGNATURA = models.AutoField(primary_key=True)
    ASIGNATURA = models.CharField(max_length=100)

class Evaluadores(models.Model):
    COD_SEDE = models.ForeignKey(Sedes, on_delete=models.CASCADE)
    COD_ASIGNATURA = models.ForeignKey(Asignaturas, on_delete=models.CASCADE)
    TOTAL = models.IntegerField()
