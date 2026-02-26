from ninja import Router
from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from typing import List
from django.contrib.auth.models import User
from decimal import Decimal
from ..models import SolicitudPresupuesto, CuentaAnalitica, Sede

router = Router()

class SolicitudOut(Schema):
    id: int
    titulo: str
    descripcion: str
    monto_a_ejecutar: Decimal
    estado: str
    colaborador_nombre: str = None 
    ubicacion_nombre: str = None
    cuenta_analitica_nombre: str = None

    # Resolvemos los nombres de las relaciones
    @staticmethod
    def resolve_colaborador_nombre(obj):
        return obj.colaborador.get_full_name()

    @staticmethod
    def resolve_ubicacion_nombre(obj):
        return obj.ubicacion.nombre

    @staticmethod
    def resolve_cuenta_analitica_nombre(obj):
        return obj.cuenta_analitica.nombre

class SolicitudIn(Schema):
    nombre_proyecto: str
    descripcion: str
    tipo_solicitud: str
    rubro_presupuestal: str
    ubicacion_id: int          # React enviará el ID seleccionado
    cuenta_analitica_id: int   # React enviará el ID seleccionado
    presupuesto_pre_aprobado: Decimal
    monto_a_ejecutar: Decimal
    # 1. Listar solicitudes (El Supervisor ve todas, el Colaborador solo las suyas)
@router.get("/list", response=List[SolicitudOut])
def listar_solicitudes(request):
    qs = SolicitudPresupuesto.objects.select_related(
        'colaborador', 'ubicacion', 'cuenta_analitica'
    )
    if request.user.is_superuser or request.user.groups.filter(name='Supervisor').exists():
        return qs.all()
    
    return qs.filter(colaborador=request.user)

@router.post("/create")
def crear_solicitud(request, data: SolicitudIn):
    # Ninja ya validó que 'data' trae todos los campos y que son del tipo correcto
    
    # Creamos la instancia en la DB
    solicitud = SolicitudPresupuesto.objects.create(
        **data.dict(),            # Desempaqueta nombre, descripción, etc.
        colaborador=request.user  # Asignamos al usuario que está logueado
    )
    
    return {"id": solicitud.id, "status": "success"}