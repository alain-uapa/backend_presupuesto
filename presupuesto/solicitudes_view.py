import json
import itertools
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from decimal import Decimal

from presupuesto import utils
from .models import Configuracion, SolicitudPresupuesto, AdjuntoSolicitud, Sede, RevisionSolicitud
from core.serializer import BaseSerializer 
from core.utils.login_required import login_required_json
from .google_drive import obtener_carpeta_en_drive, upload_to_drive, delete_from_drive
from emails.mailer import send_email
from core.utils.logging import log_error
from .utils import enviar_email_solicitud_creada, enviar_email_a_compras, FrontendRequest
#Presupuesto files
def es_supervisor(user):
    return user.groups.filter(name='Supervisor').exists() or user.is_superuser

def es_colaborador(user):
    return user.groups.filter(name='Colaborador').exists()

EXCLUDE_COLABORADOR = [
    'colaborador__password',
    'colaborador__is_staff',
    'colaborador__is_superuser',
    'colaborador__last_login'
]


def _serialize_solicitudes(qs):
    serializer = BaseSerializer(qs, exclude=EXCLUDE_COLABORADOR)
    data = serializer.serialize()
    for item in data:
        obj = next(x for x in qs if x.id == item['id'])
        item['files'] = [
            {'id': a.id, 'nombre': a.nombre, 'url_view': a.url_view,
             'es_certificado': a.es_certificado, 'aprobado': a.aprobado}
            for a in obj.adjuntos.all()
        ]
        item['review_notes'] = [
            {'id': c.id, 'contenido': c.contenido,
             'supervisor': c.supervisor.get_full_name() or c.supervisor.username,
             'fecha_creacion': c.fecha_creacion.isoformat(timespec='seconds'), 'estado': c.estado}
            for c in obj.revisiones.all()
        ]
    return data


def _build_qs(user, fecha_limite=None):
    from django.db.models import Prefetch
    base_qs = SolicitudPresupuesto.objects.select_related(
        'colaborador', 'ubicacion', 'cuenta_analitica'
    ).prefetch_related(
        'adjuntos',
        Prefetch('revisiones', queryset=RevisionSolicitud.objects.select_related('supervisor').order_by('-fecha_creacion'))
    )
    es_supervisor = user.is_superuser or user.groups.filter(name='Supervisor').exists()
    es_compra_rss = user.groups.filter(name='Compra RSS').exists()
    
    if es_compra_rsd := user.groups.filter(name='Compra RSD').exists():
        sede_codigo = 'RSD'
    elif es_compra_rco := user.groups.filter(name='Compra RCO').exists():
        sede_codigo = 'RCO'
    else:
        sede_codigo = None
    
    filtros_base = {}
    filtros_fecha = {'updated_at__gte': fecha_limite} if fecha_limite else {}
    
    if es_supervisor or es_compra_rss:
        qs_pendientes = base_qs.filter(estado='PENDIENTE', **filtros_fecha).order_by('-fecha_solicitud')
        qs_otras = base_qs.exclude(estado='PENDIENTE').filter(**filtros_fecha).order_by('-fecha_solicitud')
    elif sede_codigo:
        filtros_base['ubicacion__codigo'] = sede_codigo
        qs_pendientes = base_qs.filter(estado='PENDIENTE', **filtros_base, **filtros_fecha).order_by('-fecha_solicitud')
        qs_otras = base_qs.exclude(estado='PENDIENTE').filter(**filtros_base, **filtros_fecha).order_by('-fecha_solicitud')
    else:
        filtros_base['colaborador'] = user
        qs_pendientes = base_qs.filter(estado='PENDIENTE', **filtros_base, **filtros_fecha).order_by('-fecha_solicitud')
        qs_otras = base_qs.exclude(estado='PENDIENTE').filter(**filtros_base, **filtros_fecha).order_by('-fecha_solicitud')
    return list(itertools.chain(qs_pendientes, qs_otras))


def procesar_datos_solicitud(request, solicitud=None):
    if 'multipart/form-data' in request.content_type:
        data = request.POST
        archivos = request.FILES.getlist('files')
    else:
        data = json.loads(request.body)
        archivos = []

    if not solicitud:
        solicitud = SolicitudPresupuesto(colaborador=request.user)
    else:
        updated_at_str = data.get('updated_at')
        if updated_at_str:
            updated_at_client = parse_datetime(updated_at_str)
            if updated_at_client < solicitud.updated_at:
                raise ValueError("Versión desactualizada. La solicitud fue modificada por otro usuario. Intenta nuevamente.")

    solicitud.titulo = data.get('titulo', solicitud.titulo)
    solicitud.descripcion = data.get('descripcion', solicitud.descripcion)
    solicitud.tipo_solicitud = data.get('tipo_solicitud', solicitud.tipo_solicitud)
    solicitud.rubro_presupuestal = data.get('rubro_presupuestal', solicitud.rubro_presupuestal)

    if data.get('ubicacion_id'):
        solicitud.ubicacion_id = int(data.get('ubicacion_id'))
    if data.get('cuenta_analitica_id'):
        solicitud.cuenta_analitica_id = int(data.get('cuenta_analitica_id'))

    solicitud.monto_a_ejecutar = Decimal(data.get('monto_a_ejecutar', solicitud.monto_a_ejecutar)).quantize(Decimal('0.00'))
    solicitud.presupuesto_pre_aprobado = Decimal(data.get('presupuesto_pre_aprobado', solicitud.presupuesto_pre_aprobado)).quantize(Decimal('0.00'))
    solicitud.full_clean()
    solicitud.save()

    parent_folder_id = Configuracion.get_value('ID_FOLDER_DRIVE')
    id_destino = obtener_carpeta_en_drive(parent_folder_id)
    for f in archivos:
        resultado_drive = upload_to_drive(f, id_destino)
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
    qs = _build_qs(request.user)
    return JsonResponse({"solicitudes": _serialize_solicitudes(qs), "last_updated": timezone.now().isoformat(timespec='seconds')}, safe=False)

@login_required_json
def refresh_solicitudes(request):
    last_updated = request.GET.get('last_updated')
    if not last_updated:
        return JsonResponse({"error": "Parámetro 'last_updated' requerido"}, status=400)
    qs = _build_qs(request.user, last_updated)
    return JsonResponse({"solicitudes": _serialize_solicitudes(qs), "last_updated": timezone.now().isoformat(timespec='seconds')}, safe=False)

#@csrf_exempt
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
                'sede': nueva_solicitud.ubicacion.nombre,
                'monto_a_ejecutar': nueva_solicitud.monto_a_ejecutar,
                'url_solicitud': FrontendRequest.VIEW.url(request, nueva_solicitud.id)
            }
            enviar_email_solicitud_creada(context)        
            serializer = BaseSerializer([nueva_solicitud])
            return JsonResponse({"mensaje": "Creada con éxito", "datos": serializer.serialize()[0]}, status=201)
    except Exception as e:
        log_error(request, e, {'funcion': 'crear_solicitud'})
        return JsonResponse({"error": str(e)}, status=400)

#@csrf_exempt
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
    except ValueError as e:
        if "Versión desactualizada" in str(e):
            return JsonResponse({"error": str(e)}, status=409)
        raise
    except Exception as e:
        log_error(request, e, {'funcion': 'editar_solicitud', 'pk': pk})
        return JsonResponse({"error": str(e)}, status=400)

#@csrf_exempt
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
            solicitud.estado = nuevo_estado
            
            # Si es POR_REVISION, crear comentario obligatorio
            nueva_revision = None
            if nuevo_estado.upper() == 'POR_REVISION':
                if not comentarios:
                    return JsonResponse({"error": "El comentario es obligatorio para estado Por Revisión"}, status=400)
                nueva_revision = RevisionSolicitud.objects.create(
                    solicitud=solicitud,
                    supervisor=request.user,
                    contenido=comentarios
                )
                context = {
                    'titulo': solicitud.titulo,
                    'comentario': comentarios,
                    'sede': solicitud.ubicacion.nombre,
                    'monto_a_ejecutar': solicitud.monto_a_ejecutar,
                    'solicitante': solicitud.colaborador.get_full_name(),
                    'url_solicitud': FrontendRequest.VIEW.url(request, solicitud.id)
                }
                send_email(
                    subject='Tu solicitud requiere correcciones',
                    send_to_list=[solicitud.colaborador.email],
                    template='presupuesto/solicitud_en_revision.html',
                    context=context
                )
            
            # Si es rechazada, guardamos el comentario en el campo específico
            if nuevo_estado.upper() == 'RECHAZADA':
                solicitud.observaciones_supervisor = comentarios
            
            # 4. Guardar cambios
            solicitud.save()

            serializer = BaseSerializer([solicitud])  
            if nuevo_estado.upper() == 'RECHAZADA':          
                context = {
                    'titulo': solicitud.titulo,
                    'sede': solicitud.ubicacion.nombre,
                    'monto_a_ejecutar': solicitud.monto_a_ejecutar,
                    'url_solicitud': FrontendRequest.VIEW.url(request, solicitud.id)
                }
                email_template = 'presupuesto/solicitud_rechazada.html'
                
                send_to_list = [solicitud.colaborador.email]
                send_email(
                    subject='Solicitud de Presupuesto', 
                    send_to_list=send_to_list, 
                    template=email_template, 
                    context=context,                
                )  
            return JsonResponse({
                "mensaje": f"Estado actualizado a {nuevo_estado} con éxito",
                "newRevisionId": nueva_revision.id if nueva_revision else None
            })

        except Exception as e:
            log_error(request, e, {'funcion': 'cambiar_estado', 'pk': pk})
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido. Use PATCH"}, status=405)   

#@csrf_exempt
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

#@csrf_exempt
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

#@csrf_exempt
@login_required_json
def confirmar_solicitud(request, pk):
    """
    Vista para confirmar una solicitud de presupuesto.
    Recibe el id de la solicitud y pone el campo confirmado en True.
    """
    if request.method == 'PATCH':
        try:
            # 1. Buscar la solicitud
            try:
                solicitud = SolicitudPresupuesto.objects.get(pk=pk)
            except SolicitudPresupuesto.DoesNotExist:
                return JsonResponse({"error": "Solicitud no encontrada"}, status=400)

            # 2. Actualizar el campo confirmado
            solicitud.confirmado = True
            solicitud.save()

            return JsonResponse({
                "mensaje": "Solicitud confirmada exitosamente",
                "confirmado": True
            }, status=200)

        except Exception as e:
            log_error(request, e, {'funcion': 'confirmar_solicitud', 'pk': pk})
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido. Use PATCH"}, status=405)

@login_required_json
def cambiar_estado_revision(request, pk):
    if request.method == 'PATCH':
        try:
            try:
                revision = RevisionSolicitud.objects.get(pk=pk)
            except RevisionSolicitud.DoesNotExist:
                return JsonResponse({"error": "Revision no encontrada"}, status=404)

            data = json.loads(request.body)
            nuevo_estado = data.get('estado')

            if nuevo_estado not in ['PENDIENTE', 'RESUELTA']:
                return JsonResponse({"error": "Estado inválido. Use 'PENDIENTE' o 'RESUELTA'"}, status=400)

            revision.estado = nuevo_estado
            revision.save()

            solicitud = revision.solicitud
            if not solicitud.revisiones.exclude(estado='RESUELTA').exists():
                solicitud.estado = 'PENDIENTE'
                solicitud.save()

            return JsonResponse({
                "mensaje": f"Estado de la revision actualizado a {nuevo_estado}",
                "revision": {
                    "id": revision.id,
                    "estado": revision.estado
                },
                "solicitud": {
                    "id": solicitud.id,
                    "estado": solicitud.estado
                }
            }, status=200)

        except Exception as e:
            log_error(request, e, {'funcion': 'cambiar_estado_comentario', 'pk': pk})
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido. Use PATCH"}, status=405)