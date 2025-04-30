from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class Plan(models.Model):
    nombre = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_dias = models.IntegerField()  # Duración en días

    def __str__(self):
        return self.nombre

class Usuario(AbstractUser):
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_ingreso = models.DateField(default=timezone.now)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    es_activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.is_superuser:  # Solo aplica estas reglas a usuarios no superusuarios
            self.username = self.rut.replace('.', '').replace('-', '').upper()
            self.set_unusable_password()
        # Para superusuarios, se usará el username y la contraseña ingresados en createsuperuser

        # Calcular fecha_vencimiento solo al crear el usuario, si no se especifica manualmente
        if not self.pk and not self.fecha_vencimiento and self.plan:
            self.fecha_vencimiento = self.fecha_ingreso + relativedelta(days=self.plan.duracion_dias)
        
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
    tipo = models.CharField(max_length=1, choices=[('E', 'Entrada')])  # Solo entrada

class Meta(models.Model):
    meta_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=2000000)
    maximo_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=5000000)

class AudioPresentacion(models.Model):
    archivo = models.FileField(upload_to='audios/')
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return self.descripcion