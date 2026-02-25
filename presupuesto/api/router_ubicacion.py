from ninja import Router
from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from typing import List
from django.contrib.auth.models import User
from decimal import Decimal
from ..models import SolicitudPresupuesto, CuentaAnalitica, Sede

router = Router()

class SedeOut(Schema):
    id: int
    codigo: str
    nombre: str

@router.get("/list", response=List[SedeOut])
def listar_sedes(request):
    return Sede.objects.all().order_by('nombre')

