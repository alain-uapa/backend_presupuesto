import json
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import SolicitudPresupuesto
from core.serializer import BaseSerializer 
from core.utils.login_required import login_required_json

@login_required_json
def solicitudes_list(request):
    qs = SolicitudPresupuesto.objects.select_related(
       'colaborador', 'ubicacion', 'cuenta_analitica'
    ).only('id',
    
    # 2. Campos del Colaborador
    'colaborador__id', 
    'colaborador__first_name', 
    
    # 3. Campos de Ubicacion (Obligatorio si usas select_related)
    'ubicacion__nombre', 
    
    # 4. Campos de Cuenta Analitica (Obligatorio si usas select_related)
    'cuenta_analitica__codigo',
    'cuenta_analitica__nombre')
    # Lógica de filtrado según permisos
    if request.user.is_superuser or request.user.groups.filter(name='Supervisor').exists():
        qs = qs.all()
    else:
        qs = qs.filter(colaborador=request.user)

    # Transformamos el QuerySet a formato JSON (string)
    serializer = BaseSerializer(qs)
    return JsonResponse(serializer.serialize(), safe=False)

@csrf_exempt # Solo si no estás enviando el token CSRF desde el frontend
def crear_solicitud(request):
    if request.method == 'POST':
        try:
            # 1. Cargar los datos del cuerpo de la petición
            data = json.loads(request.body)

            # 2. Crear la instancia (Asignamos el colaborador del usuario logueado)
            nueva_solicitud = SolicitudPresupuesto(
                colaborador=request.user,
                titulo=data.get('titulo'),
                descripcion=data.get('descripcion'),
                tipo_solicitud=data.get('tipo_solicitud'),
                rubro_presupuestal=data.get('rubro_presupuestal'),
                # Obtenemos las instancias de las FK por su ID
                ubicacion_id=data.get('ubicacion'),
                cuenta_analitica_id=data.get('cuenta_analitica'),
                presupuesto_pre_aprobado=data.get('presupuesto_pre_aprobado'),
                monto_a_ejecutar=data.get('monto_a_ejecutar'),
            )

            # 3. Guardar en la base de datos
            nueva_solicitud.save()

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