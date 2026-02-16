from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from typing import List
from django.contrib.auth.models import User
from .models import SolicitudPresupuesto, CuentaAnalitica, Ubicacion
from decimal import Decimal

api = NinjaAPI(title="API Presupuesto")

class ColaboradorOut(Schema):
    id: int
    first_name: str
    last_name: str
    email: str

    @staticmethod
    def resolve_full_name(obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class UbicacionOut(Schema):
    id: int
    nombre: str

class CuentaAnaliticaOut(Schema):
    id: int
    nombre: str

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

# --- RUTAS ---

# 1. Listar solicitudes (El Supervisor ve todas, el Colaborador solo las suyas)
@api.get("/solicitudes", response=List[SolicitudOut])
def listar_solicitudes(request):
    qs = SolicitudPresupuesto.objects.select_related(
        'colaborador', 'ubicacion', 'cuenta_analitica'
    )
    print(qs.all())
    if request.user.is_superuser or request.user.groups.filter(name='Supervisor').exists():
        return qs.all()
    
    return qs.filter(colaborador=request.user)

@api.get("/colaboradores", response=List[ColaboradorOut])
def listar_colaboradores(request):
    # Traemos usuarios activos para que no aparezcan ex-empleados en la lista
    return User.objects.filter(is_active=True).order_by('first_name')

@api.get("/ubicaciones", response=List[UbicacionOut])
def listar_ubicaciones(request):
    return Ubicacion.objects.all().order_by('nombre')

@api.get("/cuentas", response=List[CuentaAnaliticaOut])
def listar_cuentas(request):
    return CuentaAnalitica.objects.all().order_by('nombre')

@api.post("/solicitudes")
def crear_solicitud(request, data: SolicitudOut):
    # Aquí Ninja valida automáticamente que 'data' cumpla el esquema
    solicitud = SolicitudPresupuesto.objects.create(
        **data.dict(exclude={'id', 'colaborador_id'}),
        colaborador=request.user
    )
    return {"id": solicitud.id, "message": "Creada con éxito"}