from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Asistencia  

from django.db.models import F

class Command(BaseCommand):
    help = 'Marca la salida automáticamente para usuarios sin salida después de 3 horas'

    def handle(self, *args, **kwargs):
        ahora = timezone.now()
        tres_horas_atras = ahora - timezone.timedelta(hours=3)

        # Obtener entradas sin salida correspondiente
        entradas_sin_salida = Asistencia.objects.filter(
            tipo='E',
            fecha_hora__lte=tres_horas_atras
        ).exclude(
            usuario__asistencia__tipo='S',
            usuario__asistencia__fecha_hora__gt=F('fecha_hora')
        )

        for entrada in entradas_sin_salida:
            Asistencia.objects.create(
                usuario=entrada.usuario,
                tipo='S',
                fecha_hora=entrada.fecha_hora + timezone.timedelta(hours=3)
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Salida marcada para {entrada.usuario.get_full_name()} a las {entrada.fecha_hora + timezone.timedelta(hours=3)}'
                )
            )