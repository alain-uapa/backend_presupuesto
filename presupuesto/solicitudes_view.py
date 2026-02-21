import time
import json
import itertools
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

from presupuesto import utils
from .models import Configuracion, SolicitudPresupuesto, AdjuntoSolicitud, Ubicacion
from core.serializer import BaseSerializer 
from core.utils.login_required import login_required_json
from .google_drive import upload_to_drive, delete_from_drive
from emails.mailer import send_email
from core.utils.logging import log_error

#Presupuesto files
def es_supervisor(user):
    return user.groups.filter(name='Supervisor').exists() or user.is_superuser

def es_colaborador(user):
    return user.groups.filter(name='Colaborador').exists()

def procesar_datos_solicitud(request, solicitud=None):
    """
    Lógica compartida para guardar o actualizar una solicitud.
    Si solicitud=None, crea una nueva.
    """
    if 'multipart/form-data' in request.content_type:
        data = request.POST
        archivos = request.FILES.getlist('files')
    else:
        data = json.loads(request.body)
        archivos = []

    # Si no existe la solicitud, la instanciamos
    if not solicitud:
        solicitud = SolicitudPresupuesto(colaborador=request.user)

    # Mapeo de campos (Crear o Editar)
    solicitud.titulo = data.get('titulo', solicitud.titulo)
    solicitud.descripcion = data.get('descripcion', solicitud.descripcion)
    solicitud.tipo_solicitud = data.get('tipo_solicitud', solicitud.tipo_solicitud)
    solicitud.rubro_presupuestal = data.get('rubro_presupuestal', solicitud.rubro_presupuestal)
    
    if data.get('ubicacion_id'):
        solicitud.ubicacion_id = int(data.get('ubicacion_id'))
    if data.get('cuenta_analitica_id'):
        solicitud.cuenta_analitica_id = int(data.get('cuenta_analitica_id'))
    
    solicitud.monto_a_ejecutar = float(data.get('monto_a_ejecutar', solicitud.monto_a_ejecutar))
    solicitud.presupuesto_pre_aprobado = float(data.get('presupuesto_pre_aprobado', solicitud.presupuesto_pre_aprobado))

    solicitud.full_clean()
    solicitud.save()

    # Procesar archivos en Drive
    ID_FOLDER_DRIVE = Configuracion.get_value('ID_FOLDER_DRIVE')
    for f in archivos:
        resultado_drive = upload_to_drive(f, ID_FOLDER_DRIVE)
        AdjuntoSolicitud.objects.create(
            solicitud=solicitud,
            nombre=f.name,
            drive_id=resultado_drive['id'],
            url_view=resultado_drive['webViewLink'],
            mime_type=f.content_type
        )
    return solicitud

@login_required_json
def solicitudes_list(request):
    base_qs = SolicitudPresupuesto.objects.select_related(
       'colaborador', 'ubicacion', 'cuenta_analitica'
    ).prefetch_related('adjuntos')
    
    if request.user.is_superuser or request.user.groups.filter(name='Supervisor').exists():
        qs_pendientes = base_qs.filter(estado='PENDIENTE').order_by('-fecha_solicitud')
        qs_otras = base_qs.exclude(estado='PENDIENTE').order_by('-fecha_solicitud')
    else:
        qs_pendientes = base_qs.filter(estado='PENDIENTE', colaborador=request.user).order_by('-fecha_solicitud')
        qs_otras = base_qs.exclude(estado='PENDIENTE').filter(colaborador=request.user).order_by('-fecha_solicitud')
    
    qs = list(itertools.chain(qs_pendientes, qs_otras))

    exclude = [
        'colaborador__password', 
        'colaborador__is_staff',
        'colaborador__is_superuser',
        'colaborador__last_login'
    ]
    serializer = BaseSerializer(qs, exclude=exclude)
    data_serializada =  serializer.serialize() 
    for item in data_serializada:
        obj_original = next(x for x in qs if x.id == item['id'])
        item['files'] = [
            {
                'id': a.id,
                'nombre': a.nombre,
                'url_view': a.url_view,
                'es_certificado': a.es_certificado
            } for a in obj_original.adjuntos.all()
        ]
    return JsonResponse(data_serializada, safe=False)

@csrf_exempt
@login_required_json
def crear_solicitud(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        with transaction.atomic():
            nueva_solicitud = procesar_datos_solicitud(request)
            
            # --- Notificación solo al crear ---
            context = {
                'id': nueva_solicitud.id,
                'titulo': nueva_solicitud.titulo,
                'solicitante': nueva_solicitud.colaborador.get_full_name(),
                'sede': str(nueva_solicitud.ubicacion),
                'monto_a_ejecutar': nueva_solicitud.monto_a_ejecutar,
                'url_sistema': utils.generar_url_frontend(f"/request/{nueva_solicitud.id}")
            }
            send_email(
                subject='Nueva Solicitud de Presupuesto',
                send_to_list=[Configuracion.get_value('GESTOR')],
                template='presupuesto/nueva_solicitud.html',
                context=context
            )

            serializer = BaseSerializer([nueva_solicitud])
            return JsonResponse({"mensaje": "Creada con éxito", "datos": serializer.serialize()[0]}, status=201)
    except Exception as e:
        log_error(request, e, {'funcion': 'crear_solicitud'})
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@login_required_json
def editar_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)    
    try:
        with transaction.atomic():
            solicitud_editada = procesar_datos_solicitud(request, solicitud=solicitud)            
            serializer = BaseSerializer([solicitud_editada])
            return JsonResponse({"mensaje": "Actualizada con éxito", "datos": serializer.serialize()[0]}, status=200)
    except Exception as e:
        log_error(request, e, {'funcion': 'editar_solicitud', 'pk': pk})
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@login_required_json                                                                                                                                                                                                                                                                                
def cambiar_estado(request, pk):
    if request.method == 'PATCH':
        try:
            # 1. Buscar la solicitud
            try:
                solicitud = SolicitudPresupuesto.objects.get(pk=pk)
            except SolicitudPresupuesto.DoesNotExist:
                return JsonResponse({"error": "Solicitud no encontrada"}, status=404)

            # 2. Leer datos del JSON
            data = json.loads(request.body)
            nuevo_estado = data.get('status')
            comentarios = data.get('comments', '')

            if not nuevo_estado:
                return JsonResponse({"error": "El campo 'status' es obligatorio"}, status=400)

            # 3. Lógica de negocio para el estado                                                                                                                                                                                   
            solicitud.estado = nuevo_estado # Asumiendo que el campo en tu modelo se llama 'estado'
            
            # Si es rechazada, guardamos el comentario en el campo específico
            if nuevo_estado.upper() == 'RECHAZADA':
                solicitud.observaciones_supervisor = comentarios
            
            # 4. Guardar cambios
            solicitud.save()

            # 5. Respuesta
            serializer = BaseSerializer([solicitud])      
            email_template = 'presupuesto/cambio_estado.html'
            context={
                'id': solicitud.id,
                'solicitante': solicitud.colaborador.get_full_name(),
                'titulo': solicitud.titulo,
                'monto_a_ejecutar': solicitud.monto_a_ejecutar,
                'estado': nuevo_estado.upper(),
                'url_sistema': utils.generar_url_frontend(f"/request/{solicitud.id}")
            }
            #TODO: bcc_list
            send_to_list = [solicitud.colaborador.email]
            gestor = Configuracion.get_value('GESTOR')
            if request.user.email != gestor:
                send_to_list.append(gestor)
            send_email(
                subject='Solicitud de Presupuesto', 
                send_to_list=send_to_list, 
                template=email_template, 
                context=context,                
            )           
            return JsonResponse({
                "mensaje": f"Estado actualizado a {nuevo_estado} con éxito",
                "datos": serializer.serialize()[0]
            })

        except Exception as e:
            log_error(request, e, {'funcion': 'cambiar_estado', 'pk': pk})
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido. Use PATCH"}, status=405)   

@csrf_exempt
@login_required_json
def eliminar_solicitud(request, pk):
    if request.method == 'DELETE':
        try:
            # 1. Buscar la solicitud
            try:
                solicitud = SolicitudPresupuesto.objects.get(pk=pk)
            except SolicitudPresupuesto.DoesNotExist:
                return JsonResponse({"error": "Solicitud no encontrada"}, status=404)

            # 2. Seguridad: Verificar permisos
            # Solo permitimos borrar si es el dueño o si es un supervisor/admin
            es_dueño = solicitud.colaborador == request.user
            if not (es_dueño or es_supervisor(request.user)):
                return JsonResponse({
                    "error": "No tienes permiso para eliminar esta solicitud"
                }, status=403)

            # 3. Opcional: Evitar borrar solicitudes ya procesadas
            if solicitud.estado.upper() in ['APROBADA', 'RECHAZADA']:
                return JsonResponse({"error": "No se puede eliminar una solicitud ya procesada"}, status=400)

            # 4. Eliminar de la base de datos
            solicitud.delete()

            return JsonResponse({"mensaje": "Solicitud eliminada con éxito"}, status=200)

        except Exception as e:
            log_error(request, e, {'funcion': 'eliminar_solicitud', 'pk': pk})
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido. Use DELETE"}, status=405)

@csrf_exempt
def eliminar_adjunto(request, pk):
    if request.method == 'DELETE':
        # Buscamos el registro del adjunto
        adjunto = get_object_or_404(AdjuntoSolicitud, id=pk)
        drive_id = adjunto.drive_id # Guardamos el ID antes de borrar el registro
        try:
            with transaction.atomic():
                # 1. Primero intentamos eliminar de Google Drive
                # Si esto falla, lanzará una excepción y no se borrará de la DB
                delete_from_drive(drive_id)                
                # 2. Si lo anterior tuvo éxito, borramos de la base de datos
                adjunto.delete()

            return JsonResponse({
                "mensaje": "Archivo eliminado correctamente de la base de datos y Google Drive"
            }, status=200)

        except Exception as e:
            # Si el error es 404, el archivo ya no está en Drive, 
            # así que procedemos a borrar el registro de la DB de todos modos.
            if "File not found" in str(e) or "404" in str(e):
                adjunto.delete()
                return JsonResponse({"mensaje": "El archivo no existía en Drive, registro local eliminado."}, status=200)     
            log_error(request, e, {'funcion': 'eliminar_adjunto', 'pk': pk})
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
@login_required_json
def upload_certificado(request, pk):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)
        archivos = request.FILES.getlist('files')
        
        if not archivos:
            return JsonResponse({"error": "No se enviaron archivos"}, status=400)
        
        ID_FOLDER_DRIVE = Configuracion.get_value('ID_FOLDER_DRIVE')
        # Codigo copiado de otra función. En este caso sólo será un archivo
        with transaction.atomic():
            for f in archivos:
                resultado_drive = upload_to_drive(f, ID_FOLDER_DRIVE)
                adjunto = AdjuntoSolicitud.objects.create(
                    solicitud=solicitud,
                    nombre=f.name,
                    drive_id=resultado_drive['id'],
                    url_view=resultado_drive['webViewLink'],
                    mime_type=f.content_type,
                    es_certificado=True
                )

        return JsonResponse({
            "mensaje": "Certificado subido con éxito"
        }, status=201)
    
    except Exception as e:
        log_error(request, e, {'funcion': 'upload_certificado', 'pk': pk})
        return JsonResponse({"error": str(e)}, status=400)