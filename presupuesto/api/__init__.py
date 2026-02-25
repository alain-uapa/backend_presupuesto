# presupuesto/api/__init__.py
from ninja import NinjaAPI
from .router_solicitudes import router as solicitudes_router
from .router_colaboradores import router as colaboradores_router
from .router_cuentas import router as cuentas_router
from .router_ubicacion import router as sede_router

api = NinjaAPI(title="Presupuesto API")

api.add_router("/solicitudes", solicitudes_router, tags=["Solicitudes"])
api.add_router("/colaboradores", colaboradores_router, tags=["Colaboradores"])
api.add_router("/sedes", sede_router, tags=["Sedes"])
api.add_router("/cuentas", cuentas_router, tags=["Cuentas"])