import json
import os
import datetime
from django.conf import settings
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.http import JsonResponse
from core.utils.login_required import login_required_json 
from presupuesto.models import DriveFolder, GoogleConfig
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

def obtener_carpeta_en_drive(parent_id_raiz):
    # 1. Generar el formato YYYY-MM
    ahora = datetime.datetime.now()
    nombre_carpeta = ahora.strftime('%Y-%m')

    # 2. Intentar obtener de nuestra Base de Datos primero (Ahorra tiempo de API)
    folder_db = DriveFolder.objects.filter(name=nombre_carpeta).first()
    if folder_db:
        return folder_db.drive_id

    # --- Si no está en DB, vamos a Google Drive ---
    creds = authtenticate() 
    service = build('drive', 'v3', credentials=creds)
    
    drive_id = None

    # 3. Buscar si ya existe en Google Drive (Evitar duplicados)
    # Corregimos la query: debe ser exacta para evitar traer carpetas similares
    query = (
        f"name = '{nombre_carpeta}' and "
        f"'{parent_id_raiz}' in parents and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    
    respuesta = service.files().list(
        q=query,
        fields='files(id, name)',
        spaces='drive',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True        
    ).execute()

    archivos = respuesta.get('files', [])

    if archivos:
        # Si existe, tomamos el ID del primer resultado
        drive_id = archivos[0]['id']
    else:
        # 4. Si no existe en Google Drive, crearla dentro de la carpeta raíz
        metadata = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id_raiz]
        }
        nueva_carpeta = service.files().create(
            body=metadata, 
            fields='id', 
            supportsAllDrives=True # Necesario si parent_id_raiz es de una Shared Drive
        ).execute()
        drive_id = nueva_carpeta.get('id')

    # 5. Guardar en nuestra DB para la próxima vez
    if drive_id:
        # Usamos update_or_create para ser más robustos
        DriveFolder.objects.update_or_create(
            name=nombre_carpeta, 
            defaults={'drive_id': drive_id}
        )
    
    return drive_id