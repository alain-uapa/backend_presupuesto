from .models import Configuracion

def generar_url_frontend(path_solicitud):
    # Obtenemos la URL base (ej: https://presupuestos.uapa.edu.do)
    base_url = Configuracion.get_value('FRONTEND_URL', 'http://localhost:3000')
    
    # Construimos la ruta hacia el componente de React
    # El path_solicitud sería algo como "/solicitudes/5"
    return f"{base_url}{path_solicitud}"