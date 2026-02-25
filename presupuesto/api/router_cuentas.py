from ninja import Router
from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from typing import List
from django.contrib.auth.models import User
from decimal import Decimal
from ..models import SolicitudPresupuesto, CuentaAnalitica, Sede

router = Router()

class CuentaAnaliticaOut(Schema):
    id: int
    nombre: str

@router.get("/list", response=List[CuentaAnaliticaOut])
def listar_cuentas(request):
    return CuentaAnalitica.objects.all().order_by('nombre')
