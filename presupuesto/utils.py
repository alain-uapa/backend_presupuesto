from django.shortcuts import get_object_or_404
from emails.mailer import send_email
from presupuesto.models import Configuracion
from .models import Sede
from enum import Enum

class FrontendRequest(Enum):
    VIEW = "/request/{id}/"
    EDIT = "/request/{id}/edit"
    CONFIRM = "/request/{id}/confirm"

    def url(self, request, solicitud_id):
        relative_url = self.value.format(id=solicitud_id)
        return request.build_absolute_uri(relative_url)


# def generar_url_frontend(request, relative_url):
#     # Obtenemos la URL base (ej: https://presupuestos.uapa.edu.do)
#     full_url = request.build_absolute_uri(relative_url)
    
#     # Construimos la ruta hacia el componente de React
#     # relative_url sería algo como "/solicitudes/5"
#     return full_url

def enviar_email_solicitud_creada(context):
    template='presupuesto/nueva_solicitud.html'            
    usuarios_value = Configuracion.get_value('CORREOS_NUEVAS_SOLICITUDES')
    if usuarios_value:
        send_to_list = [email.strip() for email in usuarios_value.replace(';', ',').split(',') if email.strip()]
    else:
        send_to_list = []     
    send_email(
                subject='Nueva Solicitud de Presupuesto',
                send_to_list=send_to_list,
                template=template,
                context=context
            )

def enviar_email_a_compras(request, solicitud):    
    email_template = 'presupuesto/emision_certificado_a_compra.html'
    sede = get_object_or_404(Sede, id=solicitud.sede)
    usuarios_value = Configuracion.get_usuarios_compra_por_sede(sede.codigo)
    if usuarios_value:
        send_to_list = [email.strip() for email in usuarios_value.replace(';', ',').split(',') if email.strip()]
    else:
        send_to_list = []   
    context={
        'concepto': solicitud.titulo,
        'monto_a_ejecutar': solicitud.monto_a_ejecutar,
        'sede': sede.nombre,
        'url_solicitud': FrontendRequest.CONFIRM.url(request, solicitud.id)
    }
    send_to_list = [context.email_solicitante]
    send_email(
        subject='Presupuesto Aprobado', 
        send_to_list=send_to_list, 
        template=email_template, 
        context=context,                
    ) 