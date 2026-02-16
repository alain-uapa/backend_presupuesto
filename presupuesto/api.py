from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from typing import List
from .models import SolicitudPresupuesto
from decimal import Decimal

api = NinjaAPI(title="API Presupuesto")

# Este es tu "Serializer" en versión Ninja (Schema)
class SolicitudOut(Schema):
    id: int
    titulo: str
    descripcion: str
    monto_a_ejecutar: Decimal
    estado: str
    # Ninja permite traer datos de relaciones fácilmente
    colaborador_id: int 
    ubicacion_id: int

# --- RUTAS ---

# 1. Listar solicitudes (El Supervisor ve todas, el Colaborador solo las suyas)
@api.get("/solicitudes", response=List[SolicitudOut])
def listar_solicitudes(request):
    if request.user.is_superuser or request.user.groups.filter(name='Supervisor').exists():
        return SolicitudPresupuesto.objects.all()
    return SolicitudPresupuesto.objects.filter(colaborador=request.user)

# 2. Crear una solicitud
@api.post("/solicitudes")
def crear_solicitud(request, data: SolicitudOut):
    # Aquí Ninja valida automáticamente que 'data' cumpla el esquema
    solicitud = SolicitudPresupuesto.objects.create(
        **data.dict(exclude={'id', 'colaborador_id'}),
        colaborador=request.user
    )
    return {"id": solicitud.id, "message": "Creada con éxito"}