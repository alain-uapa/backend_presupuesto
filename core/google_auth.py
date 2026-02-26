from django.views.decorators.csrf import ensure_csrf_cookie
import json
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.models import User,  Group
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests

from presupuesto.models import Configuracion
# Reemplaza con tu Client ID de Google Console
GOOGLE_CLIENT_ID = "478848519153-0tklbkp5d7252099relj297632eka3qg.apps.googleusercontent.com"

@csrf_exempt
@ensure_csrf_cookie #Obliga a django a enviar el token en la cookie
def google_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')

            # 1. Validar el token con Google
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

            # 2. Obtener datos del usuario
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            # 3. Buscar o crear el usuario en Django
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email, # O un generador de username
                    'first_name': first_name,
                    'last_name': last_name
                }
            )
            # 4. Iniciar sesión (Crea la cookie de sesión de Django)
            login(request, user)
            # Verificar si el usuario ya pertenece al grupo Supervisor
            es_supervisor = user.groups.filter(name='Supervisor').exists()
            
            es_usuario_compra = Configuracion.objects.filter(
                nombre__startswith='USUARIOS_COMPRA',
                valor__contains=email
            ).exists()
            
            # Determinar el grupo del usuario: si ya es Supervisor, dejarlo así
            # sino verificar si es Compra por Configuración, sino es Colaborador
            if es_supervisor:
                # Ya es Supervisor, no modificar su grupo
                rol_usuario = 'Supervisor'
            elif es_usuario_compra:
                grupo = Group.objects.get_or_create(name='Compra')[0]
                user.groups.clear()
                user.groups.add(grupo)
                rol_usuario = 'Compra'
            else:
                grupo = Group.objects.get_or_create(name='Colaborador')[0]
                user.groups.clear()
                user.groups.add(grupo)
                rol_usuario = 'Colaborador'
            
            return JsonResponse({
                "mensaje": "Sesión iniciada correctamente",
                "user": {
                        "id": user.id,
                        "email": user.email, 
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": rol_usuario
                        }
            })

        except ValueError:
            return JsonResponse({"error": "Token de Google inválido"}, status=400)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)