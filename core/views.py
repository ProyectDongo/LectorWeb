from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View
from django.contrib.auth import login
from django.contrib import messages
from .models import HuellaDigital, Usuario, Asistencia, Plan, Meta
from .forms import UsuarioForm
import base64
import json
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.db import IntegrityError, transaction
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)




@login_required
def home(request):
    rut = request.GET.get('rut', '')
    usuario_encontrado = None
    if rut:
        try:
            usuario_encontrado = Usuario.objects.get(rut=rut)
        except Usuario.DoesNotExist:
            pass

    ultimas_asistencias = Asistencia.objects.order_by('-fecha_hora')[:5]
    stats = [
        {'title': 'Miembros Activos', 'value': Usuario.objects.filter(es_activo=True).count(), 'icon': 'bi-person-check'},
        {'title': 'Entradas Hoy', 'value': Asistencia.objects.filter(tipo='E', fecha_hora__date=timezone.now().date()).count(), 'icon': 'bi-box-arrow-in-right'},
        {'title': 'Total Asistencias', 'value': Asistencia.objects.count(), 'icon': 'bi-clock-history'},
    ]

    # Cálculos de ingresos
    hoy = timezone.now().date()
    mes_actual = hoy.month
    anio_actual = hoy.year

    ingresos_diarios = Asistencia.objects.filter(fecha_hora__date=hoy).count() * 5000  # Suponiendo plan diario
    primer_dia_mes = hoy.replace(day=1)
    ingresos_mensuales = sum([u.plan.precio for u in Usuario.objects.filter(fecha_ingreso__gte=primer_dia_mes, fecha_ingreso__lte=hoy) if u.plan])
    
    # Ingresos trimestrales
    primer_dia_trimestre = hoy.replace(month=((mes_actual-1)//3)*3 + 1, day=1)
    ingresos_trimestrales = sum([u.plan.precio for u in Usuario.objects.filter(fecha_ingreso__gte=primer_dia_trimestre, fecha_ingreso__lte=hoy) if u.plan])

    # Ingresos anuales
    primer_dia_anio = hoy.replace(month=1, day=1)
    ingresos_anuales = sum([u.plan.precio for u in Usuario.objects.filter(fecha_ingreso__gte=primer_dia_anio, fecha_ingreso__lte=hoy) if u.plan])

    metas = Meta.objects.first()
    meta_mensual = metas.meta_mensual if metas else 2000000
    maximo_mensual = metas.maximo_mensual if metas else 5000000

    notificacion = None
    if ingresos_mensuales >= maximo_mensual:
        notificacion = "¡Máximo mensual alcanzado!"
    elif ingresos_mensuales >= meta_mensual:
        notificacion = "¡Meta mensual alcanzada!"

    return render(request, 'home/home.html', {
        'usuario_encontrado': usuario_encontrado,
        'ultimas_asistencias': ultimas_asistencias,
        'stats': stats,
        'ingresos_diarios': ingresos_diarios,
        'ingresos_mensuales': ingresos_mensuales,
        'ingresos_trimestrales': ingresos_trimestrales,
        'ingresos_anuales': ingresos_anuales,
        'meta_mensual': meta_mensual,
        'maximo_mensual': maximo_mensual,
        'notificacion': notificacion,
    })




@login_required
def registrar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save()
                messages.success(request, 'Miembro registrado exitosamente!')
                return redirect('home')
            except IntegrityError:
                messages.error(request, 'Error: El RUT ya está en uso.')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = UsuarioForm()
    return render(request, 'registro/registrar_usuario.html', {'form': form})




@login_required
def registro_huella(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    return render(request, 'registro/registro_huella.html', {'usuario': usuario})




@login_required
def lecto_ingreso(request):
    usuario = request.user
    return render(request, 'ingreso/lector_ingreso.html', {'user_id': usuario.id})







@method_decorator(require_http_methods(["GET", "POST"]), name='dispatch')
class FingerprintRegistrationView(View):
    def get(self, request, user_id):
        usuario = get_object_or_404(Usuario, id=user_id)
        return render(request, 'registro/registro_huella.html', {'usuario': usuario})

    def post(self, request, user_id):
        try:
            data = json.loads(request.body)
            if 'template1' not in data or 'match_score' not in data:
                return JsonResponse({'error': 'Datos incompletos'}, status=400)

            if data['match_score'] < 80:
                return JsonResponse({'error': f'Coincidencia insuficiente ({data["match_score"]}/100)'}, status=400)

            usuario = get_object_or_404(Usuario, id=user_id)
            template1 = base64.b64decode(data['template1'].split(',')[1] if ',' in data['template1'] else data['template1'])

            with transaction.atomic():
                huella, created = HuellaDigital.objects.update_or_create(
                    usuario=usuario,
                    defaults={'template': template1, 'calidad': data.get('quality', 80)}
                )
                return JsonResponse({
                    'status': 'success',
                    'message': 'Huella registrada exitosamente',
                    'redirect_url': reverse('home')
                })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
def registrar_asistencia(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            usuario = Usuario.objects.get(id=user_id)
            hoy = timezone.now().date()

            if not HuellaDigital.objects.filter(usuario=usuario).exists():
                return JsonResponse({'error': 'Huella no registrada'}, status=400)
            if not usuario.es_activo:
                return JsonResponse({'error': 'Usuario inactivo'}, status=400)
            if usuario.fecha_vencimiento < hoy:
                return JsonResponse({'error': 'Membresía expirada'}, status=400)

            entradas_hoy = Asistencia.objects.filter(usuario=usuario, fecha_hora__date=hoy)
            if entradas_hoy.count() >= 3:
                return JsonResponse({'error': 'Límite de 3 entradas diarias alcanzado'}, status=400)

            Asistencia.objects.create(usuario=usuario, tipo='E', fecha_hora=timezone.now())
            mensaje = f'Bienvenido, le quedan {(usuario.fecha_vencimiento - hoy).days} días de membresía'

            return JsonResponse({
                'status': 'success',
                'hora': timezone.now().strftime('%H:%M:%S'),
                'mensaje': mensaje,
                'audio': '/static/audio/entrada.mp3'  # Audio de 5 segundos
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)






@csrf_exempt
def verificar_huella(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_b64 = data.get('template')
            if not template_b64:
                return JsonResponse({'error': 'Template no proporcionado'}, status=400)

            template_bytes = base64.b64decode(template_b64)
            huellas = HuellaDigital.objects.all()

            for huella in huellas:
                stored_template_b64 = base64.b64encode(huella.template).decode('utf-8')
                match_response = requests.post(
                    'http://localhost:9000/match',
                    json={'template1': template_b64, 'template2': stored_template_b64}
                )
                if match_response.ok and match_response.json().get('score', 0) >= 80:
                    usuario = huella.usuario
                    if not usuario.es_activo:
                        return JsonResponse({'error': 'Cuenta inactiva'}, status=400)
                    if usuario.fecha_vencimiento < timezone.now().date():
                        return JsonResponse({'error': 'Membresía expirada'}, status=400)

                    return JsonResponse({
                        'existe': True,
                        'usuario': {
                            'id': usuario.id,
                            'nombre': f"{usuario.first_name} {usuario.last_name}",
                            'rut': usuario.rut,
                            'vencimiento': usuario.fecha_vencimiento.strftime('%d/%m/%Y'),
                            'activo': usuario.es_activo
                        }
                    })
            return JsonResponse({'existe': False})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)






@login_required
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos actualizados correctamente!')
            return redirect('home')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'registro/editar_usuario.html', {'form': form})





@login_required
def eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if request.method == 'POST':
        usuario.delete()
        return redirect('home')
    return render(request, 'confirmacion.html', {'usuario': usuario})






@csrf_exempt
@require_http_methods(["POST"])
def registrar_entrada_rut(request):
    try:
        data = json.loads(request.body)
        rut = data.get('rut')
        if not rut:
            return JsonResponse({'error': 'RUT no proporcionado'}, status=400)

        usuario = Usuario.objects.get(rut=rut)
        hoy = timezone.now().date()

        if not usuario.es_activo:
            return JsonResponse({'error': 'Usuario inactivo'}, status=400)
        if usuario.fecha_vencimiento < hoy:
            return JsonResponse({'error': 'Membresía expirada'}, status=400)

        entradas_hoy = Asistencia.objects.filter(usuario=usuario, fecha_hora__date=hoy)
        if entradas_hoy.count() >= 3:
            return JsonResponse({'error': 'Límite de 3 entradas diarias alcanzado'}, status=400)

        Asistencia.objects.create(usuario=usuario, tipo='E', fecha_hora=timezone.now())
        return JsonResponse({
            'status': 'success',
            'usuario_nombre': usuario.get_full_name(),
            'audio': '/static/audio/entrada.mp3'
        })
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)