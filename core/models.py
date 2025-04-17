from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class Usuario(AbstractUser):
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_ingreso = models.DateField(default=timezone.now)
    modo_pago = models.PositiveSmallIntegerField(
        choices=[(1, '1 mes'), (2, '2 meses'), (3, '3 meses')], 
        default=1
    )
    fecha_vencimiento = models.DateField()
    es_activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.fecha_vencimiento = self.fecha_ingreso + relativedelta(months=self.modo_pago)
        super().save(*args, **kwargs)

class HuellaDigital(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='huella')
    template = models.BinaryField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    calidad = models.IntegerField(default=80)

    def __str__(self):
        return f"Huella de {self.usuario.get_full_name()}"

class Asistencia(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=1, choices=[('E', 'Entrada'), ('S', 'Salida')])