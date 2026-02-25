import json
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import Sede, CuentaAnalitica
from core.serializer import BaseSerializer 
from core.utils.login_required import login_required_json

#@login_required_json
def ubicaciones_list(request):
    # Traemos todas las ubicaciones ordenadas por nombre
    qs = Sede.objects.all().order_by('nombre')
    
    # El serializer procesará 'id' y 'nombre' automáticamente
    serializer = BaseSerializer(qs)
    return JsonResponse(serializer.serialize(), safe=False)

#@login_required_json
def cuentas_analiticas_list(request):
    # Traemos las cuentas analíticas
    qs = CuentaAnalitica.objects.all().order_by('nombre')
    
    # El serializer procesará 'id', 'codigo' y 'nombre'
    serializer = BaseSerializer(qs, exclude=['codigo'])
    return JsonResponse(serializer.serialize(), safe=False)