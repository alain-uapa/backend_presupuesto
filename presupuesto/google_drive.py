import json
import os
from django.conf import settings
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.http import JsonResponse
from core.utils.login_required import login_required_json 
from presupuesto.models import GoogleConfig
"""
Sube cualquier tipo de archivo a Google Drive.
archivo_django: El objeto que viene de request.FILES
folder_id: El ID de la carpeta de Drive donde se guardará
"""

def authtenticate():
    #SERVICE_ACCOUNT_FILE = 'amiable-hydra-487802-a4-32ee1359e589.json'
    #json_path = os.path.join(settings.BASE_DIR, SERVICE_ACCOUNT_FILE)
    
    # Normaliza la ruta (limpia los ../..)
    #json_path = os.path.normpath(json_path)
    # Verificación de seguridad para depurar
    #if not os.path.exists(json_path):
    #    raise FileNotFoundError(f"No se encontró el archivo de credenciales en: {json_path}")
    # Obtenemos la configuración activa
    config = GoogleConfig.objects.filter(activo=True).first()
    
    if not config:
        raise ValueError("No hay una configuración de Google Drive activa en la BD")

    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_info(
        config.credentials_json, scopes=SCOPES)
    return creds

@login_required_json
def uploadfile(request):
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        
        # Validar extensiones permitidas (Opcional pero recomendado)
        extensiones_permitidas = [
            'application/pdf', 
            'image/jpeg', 
            'image/png', 
            'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        if archivo.content_type not in extensiones_permitidas:
            return JsonResponse({"error": "Tipo de archivo no permitido"}, status=400)

        # Llamamos a la función genérica
        resultado = upload_to_drive(archivo, 'ID_DE_TU_CARPETA')
        
        return JsonResponse({
            "mensaje": "Archivo subido con éxito",
            "drive_id": resultado.get('id'),
            "url": resultado.get('webViewLink')
        })

def upload_to_drive(archivo_django, folder_id, mimetype=None):

    creds = authtenticate()
    service = build('drive', 'v3', credentials=creds)

    if mimetype is None:
        mimetype = archivo_django.content_type 

    file_metadata = {
        'name': archivo_django.name,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(
        archivo_django.file, 
        mimetype=mimetype, # Aquí pasamos image/jpeg, application/pdf, etc.
        resumable=True
    )
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink',
        supportsAllDrives=True
    ).execute()

    return file

def delete_from_drive(file_id):
    """
    Elimina un archivo de Google Drive dado su ID.
    """
    creds = authtenticate() # Tu función de autenticación
    service = build('drive', 'v3', credentials=creds)
    # Es importante usar supportsAllDrives=True porque estamos en un Shared Drive
    service.files().delete(
        fileId=file_id, 
        supportsAllDrives=True
    ).execute()