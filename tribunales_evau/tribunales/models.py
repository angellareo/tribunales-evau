from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Sede(models.Model):
    COD_SEDE = models.AutoField(primary_key=True)
    UBICACION = models.CharField(max_length=100)


class Asignatura(models.Model):
    COD_ASIGNATURA = models.AutoField(primary_key=True)
    ASIGNATURA = models.CharField(max_length=100)


class Examen(models.Model):
    # id = CompositeKey(columns=['COD_SEDE', 'COD_ASIGNATURA', 'FECHA'])
    COD_SEDE = models.ForeignKey(Sede, on_delete=models.CASCADE)
    COD_ASIGNATURA = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    FECHA = models.DateField()
    EXAMENES = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Examenes"
        constraints = [models.UniqueConstraint(fields=["COD_SEDE", "COD_ASIGNATURA", "FECHA"], name="unique_examen")]


class Evaluador(models.Model):
    COD_SEDE = models.ForeignKey(Sede, on_delete=models.CASCADE)
    COD_ASIGNATURA = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    EVALUADORES = models.IntegerField()

    class Meta:
        verbose_name_plural = "Evaluadores"
        constraints = [models.UniqueConstraint(fields=["COD_SEDE", "COD_ASIGNATURA"], name="unique_evaluador")]


@receiver(post_save, sender=Examen)
def invalidate_cache(sender, instance, **kwargs):
    cache.clear()
