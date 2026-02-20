import time
import json
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

ID_FOLDER_DRIVE = '0AO2iR5vQLMy7Uk9PVA' #Presupuesto files
def es_supervisor(user):
    return user.groups.filter(name='Supervisor').exists() or user.is_superuser

def es_colaborador(user):
    return user.groups.filter(name='Colaborador').exists()

@login_required_json
def solicitudes_list(request):
    qs = SolicitudPresupuesto.objects.select_related(
       'colaborador', 'ubicacion', 'cuenta_analitica'
    ).prefetch_related('adjuntos')
    """.only('id',
    
    # 2. Campos del Colaborador
    'colaborador__id', 
    'colaborador__first_name', 
    
    # 3. Campos de Ubicacion (Obligatorio si usas select_related)
    'ubicacion__nombre', 
    
    # 4. Campos de Cuenta Analitica (Obligatorio si usas select_related)
    'cuenta_analitica__codigo',
    'cuenta_analitica__nombre')
    """
    qs = qs.all()
    # Lógica de filtrado según permisos
    if request.user.is_superuser or request.user.groups.filter(name='Supervisor').exists():
       qs = qs.all()
    else:
       qs = qs.filter(colaborador=request.user)

    # Transformamos el QuerySet a formato JSON (string)
    exclude = [
        'colaborador__password', 
        'colaborador__is_staff',
        'colaborador__is_superuser',
        'colaborador__last_login'
    ]
    serializer = BaseSerializer(qs, exclude=exclude)
    data_serializada =  serializer.serialize() 
    for item in data_serializada:
        # Buscamos el objeto original en el queryset para sacar sus adjuntos
        obj_original = next(x for x in qs if x.id == item['id'])
        item['files'] = [
            {
                'id': a.id,
                'nombre': a.nombre,
                'url_view': a.url_view
            } for a in obj_original.adjuntos.all()
        ]
    #time.sleep(5)
    return JsonResponse(data_serializada, safe=False)

@csrf_exempt # Solo si no estás enviando el token CSRF desde el frontend
@login_required_json
def crear_solicitud(request):
    if request.method == 'POST':
        # 1. Envolver todo en un bloque atómico
        try:
            with transaction.atomic():
                # --- Parseo de datos ---
                if 'multipart/form-data' in request.content_type:              
                    data = request.POST  
                    archivos = request.FILES.getlist('files')
                else:
                    data = json.loads(request.body)
                    archivos = []

                # --- Creación del registro principal ---
                nueva_solicitud = SolicitudPresupuesto(
                    colaborador=request.user,
                    titulo=data.get('titulo'),
                    descripcion=data.get('descripcion'),
                    tipo_solicitud=data.get('tipo_solicitud'),
                    rubro_presupuestal=data.get('rubro_presupuestal'),
                    ubicacion_id=int(data.get('ubicacion_id')) if data.get('ubicacion_id') else None,
                    cuenta_analitica_id=int(data.get('cuenta_analitica_id')) if data.get('cuenta_analitica_id') else None,
                    monto_a_ejecutar=float(data.get('monto_a_ejecutar', 0)),
                    presupuesto_pre_aprobado=float(data.get('presupuesto_pre_aprobado', 0))
                )
                
                # Validar y guardar (Si falla aquí, no se llega a Drive)
                nueva_solicitud.full_clean()
                nueva_solicitud.save()

                # --- Procesamiento de Adjuntos ---
                for f in archivos:
                    # Si upload_to_drive falla (ej. error 403), lanzará una excepción
                    # y transaction.atomic hará rollback de 'nueva_solicitud' automáticamente.
                    resultado_drive = upload_to_drive(f, ID_FOLDER_DRIVE)
                    
                    AdjuntoSolicitud.objects.create(
                        solicitud=nueva_solicitud,
                        nombre=f.name,
                        drive_id=resultado_drive['id'],
                        url_view=resultado_drive['webViewLink'],
                        mime_type=f.content_type
                    )
                email_template = 'presupuesto/nueva_solicitud.html'       
                frontend_url = utils.generar_url_frontend(f"/solicitudes/{nueva_solicitud.id}")         
                context={
                    'id': nueva_solicitud.id,
                    'titulo': nueva_solicitud.titulo,
                    'solicitante': nueva_solicitud.colaborador.get_full_name(),
                    'sede': str(nueva_solicitud.ubicacion),
                    'monto_a_ejecutar': nueva_solicitud.monto_a_ejecutar,
                    'url_sistema': frontend_url
                }
                gestor = Configuracion.get_value('GESTOR')
                send_to_list = [gestor]                
                send_email(
                    subject='Solicitud de Presupuesto', 
                    send_to_list=send_to_list, 
                    template=email_template, 
                    context=context,                
                )           
                # --- Respuesta Final ---
                serializer = BaseSerializer([nueva_solicitud])
                return JsonResponse({
                    "mensaje": "Solicitud y adjuntos creados con éxito",
                    "datos": serializer.serialize()[0]
                }, status=201)

        except Exception as e:
            # Al capturar la excepción aquí, Django ya hizo el rollback de la DB
            # por haber salido del bloque 'with transaction.atomic()' con un error.
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
@login_required_json
def editar_solicitud(request, pk):
    # Obtenemos la solicitud o lanzamos 404 si no existe
    solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # --- 1. Parseo de datos ---
                if 'multipart/form-data' in request.content_type:              
                    data = request.POST                      
                    archivos = request.FILES.getlist('files')                    
                else:
                    data = json.loads(request.body)
                    archivos = []

                # --- 2. Actualización de campos de la solicitud ---
                # Usamos los datos nuevos o mantenemos los actuales si no vienen en el POST
                solicitud.titulo = data.get('titulo', solicitud.titulo)
                solicitud.descripcion = data.get('descripcion', solicitud.descripcion)
                solicitud.tipo_solicitud = data.get('tipo_solicitud', solicitud.tipo_solicitud)
                solicitud.rubro_presupuestal = data.get('rubro_presupuestal', solicitud.rubro_presupuestal)
                
                # Manejo de IDs y montos
                if data.get('ubicacion_id'):
                    solicitud.ubicacion_id = int(data.get('ubicacion_id'))
                if data.get('cuenta_analitica_id'):
                    solicitud.cuenta_analitica_id = int(data.get('cuenta_analitica_id'))
                
                solicitud.monto_a_ejecutar = float(data.get('monto_a_ejecutar', solicitud.monto_a_ejecutar))
                solicitud.presupuesto_pre_aprobado = float(data.get('presupuesto_pre_aprobado', solicitud.presupuesto_pre_aprobado))
                
                # Validar y guardar cambios en el registro principal
                solicitud.full_clean()
                solicitud.save()

                # --- 3. Procesamiento de NUEVOS Adjuntos ---
                # Al igual que en crear, si Drive falla, se deshacen los cambios del paso 2
                for f in archivos:
                    resultado_drive = upload_to_drive(f, ID_FOLDER_DRIVE)
                    
                    AdjuntoSolicitud.objects.create(
                        solicitud=solicitud, # Asociamos a la misma solicitud
                        nombre=f.name,
                        drive_id=resultado_drive['id'],
                        url_view=resultado_drive['webViewLink'],
                        mime_type=f.content_type
                    )

                # --- 4. Respuesta ---
                serializer = BaseSerializer([solicitud])
                return JsonResponse({
                    "mensaje": "Solicitud actualizada y archivos añadidos con éxito",
                    "datos": serializer.serialize()[0]
                }, status=200)

        except Exception as e:
            # Rollback automático de los cambios en 'solicitud' si falla la subida a Drive
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

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
                'url_sistema': request.build_absolute_uri(f"/solicitudes/{solicitud.id}")
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
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)