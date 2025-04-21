from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View
from django.contrib.auth import login
from django.contrib import messages
from .models import HuellaDigital, Usuario, Asistencia
from .forms import UsuarioForm
import base64
import json
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.forms.models import model_to_dict
from django.urls import reverse
from django.db import IntegrityError, transaction
import requests
import logging

logger = logging.getLogger(__name__)

#INGRESO DE USUARIO












# Configure logger

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
        {'title': 'Salidas Hoy', 'value': Asistencia.objects.filter(tipo='S', fecha_hora__date=timezone.now().date()).count(), 'icon': 'bi-box-arrow-right'},
        {'title': 'Total Asistencias', 'value': Asistencia.objects.count(), 'icon': 'bi-clock-history'},
    ]

    return render(request, 'home/home.html', {
        'usuario_encontrado': usuario_encontrado,
        'ultimas_asistencias': ultimas_asistencias,
        'stats': stats,
    })





# Vista para actualizar membresía
@login_required
def actualizar_membresia(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    hoy = timezone.now().date()
    usuario.fecha_vencimiento = hoy + timezone.timedelta(days=30)
    usuario.save()
    messages.success(request, f'Membresía de {usuario.get_full_name()} actualizada por 30 días.')
    return redirect(reverse('home/home') + f'?rut={usuario.rut}')











#-------------------------------------------------------------------------------------------------
@login_required
def registrar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save(commit=False)
                # El username se establece en el método save del modelo
                usuario.save()
                messages.success(request, 'Miembro registrado exitosamente!')
                return redirect('home')
            except IntegrityError:
                messages.error(request, 'Error: El RUT ya está en uso.')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = UsuarioForm()
    return render(request, 'registro/registrar_usuario.html', {'form': form})










#-------------------------------------------------------------------------------------------------
# Vista para registrar huella digital
@login_required
def registro_huella(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    return render(request, 'registro/registro_huella.html', {'usuario': usuario})
#-------------------------------------------------------------------------------------------------
# Vista para registrar huella digital
@login_required
def lecto_ingreso(request):
    usuario = request.user
    return render(request, 'ingreso/lector_ingreso.html', {'user_id': usuario.id})

#-------------------------------------------------------------------------------------------------
# Vista para registrar huella digital   
@method_decorator(require_http_methods(["GET", "POST"]), name='dispatch')
class FingerprintRegistrationView(View):
    def get(self, request, user_id):
        usuario = get_object_or_404(Usuario, id=user_id)
        return render(request, 'registro/registro_huella.html', {'usuario': usuario})

    def post(self, request, user_id):
        try:
            data = json.loads(request.body)
            logger.debug(f"Datos recibidos: {json.dumps(data, indent=2)[:500]}...")

            # Validación de campos requeridos
            required_fields = ['template1', 'template2', 'match_score']
            if not all(field in data for field in required_fields):
                missing = [field for field in required_fields if field not in data]
                logger.error(f"Campos faltantes: {missing}")
                return JsonResponse({'error': f'Campos requeridos faltantes: {", ".join(missing)}'}, status=400)

            # Validar score mínimo (ya validado en frontend, pero reforzamos aquí)
            if data['match_score'] < 80:
                logger.warning(f"Score insuficiente: {data['match_score']}")
                return JsonResponse({'error': f'Coincidencia insuficiente ({data["match_score"]}/100)'}, status=400)

            usuario = get_object_or_404(Usuario, id=user_id)

            # Decodificar template
            try:
                template1 = base64.b64decode(data['template1'].split(',')[1] if ',' in data['template1'] else data['template1'])
            except Exception as e:
                logger.error(f"Error decodificando template: {str(e)}")
                return JsonResponse({'error': 'Formato de huella inválido'}, status=400)

            # Verificar duplicados (simplificado para evitar demoras)
            existing_prints = HuellaDigital.objects.exclude(usuario=usuario)
            for huella in existing_prints:
                existing_template = base64.b64encode(huella.template).decode('utf-8')
                match_response = requests.post(
                    'http://localhost:9000/match',
                    json={'template1': data['template1'], 'template2': existing_template},
                    timeout=2
                )
                if match_response.ok and match_response.json().get('score', 0) >= 80:
                    logger.warning(f"Huella duplicada para usuario {huella.usuario.id}")
                    return JsonResponse({
                        'error': f'Huella ya registrada para: {huella.usuario.get_full_name()}'
                    }, status=409)

            # Guardar huella
            with transaction.atomic():
                huella, created = HuellaDigital.objects.update_or_create(
                    usuario=usuario,
                    defaults={
                        'template': template1,
                        'calidad': data.get('quality', 80),
                        
                    }
                )
                logger.info(f"Huella {'creada' if created else 'actualizada'}. ID: {huella.id}")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Huella registrada exitosamente',
                    'redirect_url': reverse('home')
                })

        except json.JSONDecodeError:
            logger.error("Error decodificando JSON")
            return JsonResponse({'error': 'Formato de datos inválido'}, status=400)
        except Exception as e:
            logger.exception("Error inesperado:")
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
















#-------------------------------------------------------------------------------------------------
# Vista para registrar asistencia
@csrf_exempt
def registrar_asistencia(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            tipo = data.get('tipo')
            
            usuario = Usuario.objects.get(id=user_id)
            hoy = timezone.now().date()

            # Verificar si el usuario tiene huella registrada
            if not HuellaDigital.objects.filter(usuario=usuario).exists():
                return JsonResponse({'error': 'Huella no registrada'}, status=400)

            # Verificar estado del usuario
            if not usuario.es_activo:
                return JsonResponse({'error': 'Usuario inactivo'}, status=400)

            # Verificar si tiene deuda (fecha_vencimiento < hoy)
            if usuario.fecha_vencimiento < hoy:
                return JsonResponse({'error': 'Usted tiene una deuda pendiente'}, status=400)

            # Calcular días restantes de membresía
            dias_restantes = (usuario.fecha_vencimiento - hoy).days

            # Validar límites de registros diarios
            registros_hoy = Asistencia.objects.filter(
                usuario=usuario,
                fecha_hora__date=hoy,
                tipo=tipo
            )
            if registros_hoy.count() >= 3:
                return JsonResponse({
                    'error': f'Límite de 3 {tipo}s diarias alcanzado'
                }, status=400)

            # Validar secuencia entrada/salida
            if tipo == 'S':
                ultima_entrada = Asistencia.objects.filter(
                    usuario=usuario,
                    tipo='E',
                    fecha_hora__date=hoy
                ).last()
                if not ultima_entrada:
                    return JsonResponse({
                        'error': 'No hay entrada registrada para esta salida'
                    }, status=400)

            # Crear registro de asistencia
            Asistencia.objects.create(
                usuario=usuario,
                tipo=tipo,
                fecha_hora=timezone.now()
            )

            # Mensaje personalizado
            if tipo == 'E':
                mensaje = f'Bienvenido, le quedan {dias_restantes} días de membresía'
            else:
                mensaje = 'Hasta luego'

            return JsonResponse({
                'status': 'success',
                'hora': timezone.now().strftime('%H:%M:%S'),
                'mensaje': mensaje
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)
















#-------------------------------------------------------------------------------------------------
#Vista para verificar huella digital
@csrf_exempt
def verificar_huella(request):
    if request.method == 'POST':
        try:
            # Decodificar el cuerpo de la solicitud
            data = json.loads(request.body)
            template_b64 = data.get('template')
            
            # Validar que el template esté presente
            if not template_b64:
                logger.warning("Solicitud sin template")
                return JsonResponse({'error': 'Template no proporcionado'}, status=400)
            
            # Decodificar el template de base64 a bytes
            try:
                template_bytes = base64.b64decode(template_b64)
            except Exception as e:
                logger.error(f"Error decodificando template: {str(e)}")
                return JsonResponse({'error': 'Formato de template inválido'}, status=400)
            
            # Obtener todas las huellas registradas
            huellas = HuellaDigital.objects.all()
            if not huellas:
                logger.info("No hay huellas registradas en la base de datos")
                return JsonResponse({'existe': False})
            
            # Comparar con el SDK
            for huella in huellas:
                stored_template_b64 = base64.b64encode(huella.template).decode('utf-8')
                
                # Enviar al servicio del SDK para comparación
                match_response = requests.post(
                    'http://localhost:9000/match',
                    json={'template1': template_b64, 'template2': stored_template_b64}
                )
                
                if match_response.ok:
                    match_data = match_response.json()
                    score = match_data.get('score', 0)
                    
                    # Umbral de coincidencia (ajusta según el SDK y tus necesidades)
                    if score >= 80:
                        usuario = huella.usuario
                        
                        # Validar estado del usuario
                        if not usuario.es_activo:
                            logger.info(f"Usuario {usuario.id} inactivo")
                            return JsonResponse({'error': 'Cuenta inactiva'}, status=400)
                        if usuario.fecha_vencimiento < timezone.now().date():
                            logger.info(f"Usuario {usuario.id} con membresía expirada")
                            return JsonResponse({'error': 'Membresía expirada'}, status=400)
                        
                        # Preparar datos del usuario
                        user_data = {
                            'id': usuario.id,
                            'nombre': f"{usuario.first_name} {usuario.last_name}",
                            'rut': usuario.rut,
                            'vencimiento': usuario.fecha_vencimiento.strftime('%d/%m/%Y'),
                            'activo': usuario.es_activo
                        }
                        logger.info(f"Huella verificada para usuario {usuario.id} con score {score}")
                        return JsonResponse({'existe': True, 'usuario': user_data})
            
            logger.info("Huella no encontrada tras comparación")
            return JsonResponse({'existe': False})
        
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON del cuerpo de la solicitud")
            return JsonResponse({'error': 'Formato de datos inválido'}, status=400)
        except Exception as e:
            logger.exception(f"Error inesperado en verificar_huella: {str(e)}")
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)
    
    logger.warning(f"Método no permitido: {request.method}")
    return JsonResponse({'error': 'Método no permitido'}, status=405)


















#-------------------------------------------------------------------------------------------------
# views.py
@login_required
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()  # El método save del modelo ajusta el username y la contraseña
            messages.success(request, 'Datos actualizados correctamente!')
            return redirect('home')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'registro/editar_usuario.html', {'form': form})

#-------------------------------------------------------------------------------------------------
# Vista para eliminar usuario
def eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if request.method == 'POST':
        usuario.delete()
        return redirect('home')  # Redirige a la página principal tras eliminar
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

        # Verificar estado del usuario
        if not usuario.es_activo:
            return JsonResponse({'error': 'Usuario inactivo'}, status=400)
        if usuario.fecha_vencimiento < hoy:
            return JsonResponse({'error': 'Membresía expirada'}, status=400)

        # Validar límite de entradas diarias
        entradas_hoy = Asistencia.objects.filter(
            usuario=usuario,
            tipo='E',
            fecha_hora__date=hoy
        )
        if entradas_hoy.count() >= 3:
            return JsonResponse({'error': 'Límite de 3 entradas diarias alcanzado'}, status=400)

        # Registrar entrada
        Asistencia.objects.create(
            usuario=usuario,
            tipo='E',
            fecha_hora=timezone.now()
        )

        return JsonResponse({
            'status': 'success',
            'usuario_nombre': usuario.get_full_name()
        })
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)