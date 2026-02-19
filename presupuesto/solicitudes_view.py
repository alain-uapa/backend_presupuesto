import time
import json
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import SolicitudPresupuesto, AdjuntoSolicitud
from core.serializer import BaseSerializer 
from core.utils.login_required import login_required_json
from .upload_to_drive import upload_to_drive

ID_FOLDER_DRIVE = '1SHi0fIHmNJsyVs_J0bOYmZACrE566sqo' #Presupuesto files
def es_supervisor(user):
    return user.groups.filter(name='Supervisor').exists() or user.is_superuser

def es_colaborador(user):
    return user.groups.filter(name='Colaborador').exists()

@login_required_json
def solicitudes_list(request):
    qs = SolicitudPresupuesto.objects.select_related(
       'colaborador', 'ubicacion', 'cuenta_analitica'
    )
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
    #time.sleep(5)
    return JsonResponse(serializer.serialize(), safe=False)

@csrf_exempt # Solo si no estás enviando el token CSRF desde el frontend
@login_required_json
def crear_solicitud(request):
    if request.method == 'POST':
        try:
            if 'multipart/form-data' in request.content_type:              
                data = request.POST  
                archivos = request.FILES.getlist('files') # 'documentos' es el nombre en React   \                           
            else:
                data = json.loads(request.body)
                archivos = []

            # 2. Crear la instancia (Asignamos el colaborador del usuario logueado)
            nueva_solicitud = SolicitudPresupuesto(
                colaborador=request.user,
                titulo=data.get('titulo'),
                descripcion=data.get('descripcion'),
                tipo_solicitud=data.get('tipo_solicitud'),
                rubro_presupuestal=data.get('rubro_presupuestal'),
                # Obtenemos las instancias de las FK por su ID
                ubicacion_id=int(data.get('ubicacion_id')) if data.get('ubicacion_id') else None,
                cuenta_analitica_id=int(data.get('cuenta_analitica_id')) if data.get('cuenta_analitica_id') else None,
                monto_a_ejecutar=float(data.get('monto_a_ejecutar', 0)),
                presupuesto_pre_aprobado=float(data.get('presupuesto_pre_aprobado', 0))
            )         
            # 3. Guardar en la base de datos
            nueva_solicitud.save()
            for f in archivos:
                # Subida real a Google Drive usando tu función de Service Account
                resultado_drive = upload_to_drive(f, ID_FOLDER_DRIVE)
                
                # Guardar la referencia en la base de datos
                AdjuntoSolicitud.objects.create(
                    solicitud=nueva_solicitud,
                    nombre=f.name,
                    drive_id=resultado_drive['id'],
                    url_view=resultado_drive['webViewLink'],
                    mime_type=f.content_type
                )
            # 4. Devolver la solicitud creada (usando tu serializer para confirmación)
            # Pasamos una lista con el objeto para que el serializer funcione
            serializer = BaseSerializer([nueva_solicitud])
            return JsonResponse({
                "mensaje": "Solicitud creada con éxito",
                "datos": serializer.serialize()[0]
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
@login_required_json
def editar_solicitud(request, pk):
    if request.method == 'PUT':
        try:
            # 1. Buscar la solicitud existente
            try:
                solicitud = SolicitudPresupuesto.objects.get(pk=pk)
            except SolicitudPresupuesto.DoesNotExist:
                return JsonResponse({"error": "Solicitud no encontrada"}, status=404)

            # 2. Seguridad: ¿Tiene permiso para editarla?
            # (Ejemplo: Solo el dueño o un supervisor)
            #if solicitud.colaborador != request.user and not request.user.is_superuser:
            #     return JsonResponse({"error": "No tienes permiso para editar esta solicitud"}, status=403)

            # 3. Leer los datos del JSON
            data = json.loads(request.body)

            # 4. Actualizar los campos (solo los que vengan en el JSON)
            solicitud.titulo = data.get('titulo', solicitud.titulo)
            solicitud.descripcion = data.get('descripcion', solicitud.descripcion)
            solicitud.tipo_solicitud = data.get('tipo_solicitud', solicitud.tipo_solicitud)
            solicitud.rubro_presupuestal = data.get('rubro_presupuestal', solicitud.rubro_presupuestal)
            solicitud.presupuesto_pre_aprobado = data.get('presupuesto_pre_aprobado', solicitud.presupuesto_pre_aprobado)
            solicitud.monto_a_ejecutar = data.get('monto_a_ejecutar', solicitud.monto_a_ejecutar)
            # Actualización de llaves foráneas por ID
            if 'ubicacion_id' in data:
                solicitud.ubicacion_id = data.get('ubicacion_id')
            if 'cuenta_analitica_id' in data:
                solicitud.cuenta_analitica_id = data.get('cuenta_analitica_id')

            # 5. Guardar cambios
            solicitud.save()

            # 6. Devolver el objeto actualizado
            serializer = BaseSerializer([solicitud])
            return JsonResponse({
                "mensaje": "Solicitud actualizada con éxito",
                "datos": serializer.serialize()[0]
            })

        except Exception as e:
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