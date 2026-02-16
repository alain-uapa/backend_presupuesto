from ninja import Router
from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from typing import List
from django.contrib.auth.models import User
from decimal import Decimal
from ..models import SolicitudPresupuesto, CuentaAnalitica, Ubicacion

router = Router()

class ColaboradorOut(Schema):
    id: int
    first_name: str
    last_name: str
    email: str

    @staticmethod
    def resolve_full_name(obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

@router.get("/list", response=List[ColaboradorOut])
def listar_colaboradores(request):
    # Traemos usuarios activos para que no aparezcan ex-empleados en la lista
    return User.objects.filter(is_active=True).order_by('first_name')
