# emails/mailer.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email(*, subject, send_to_list, bcc_list=None, sender=None, template=None, context=None, html_body=None):
    """
    Envía un email usando una plantilla (.html) o un string de HTML directo.
    """
    from_email = sender or getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@uapa.edu.com')
    
    # 1. Determinar el contenido HTML
    if template:
        # Prioridad a la plantilla si se proporciona 
        html_final = render_to_string(template, context or {})
    elif html_body:
        # Si no hay template, usamos el HTML hardcoded
        html_final = html_body
    else:
        raise ValueError("Debes proporcionar un 'template' o un 'html_body'.")

    # 2. Generar versión en texto plano para compatibilidad
    text_content = strip_tags(html_final) 

    # 3. Configurar y enviar
    msg = EmailMultiAlternatives(subject=subject, 
        body=text_content, 
        from_email=from_email, 
        to=send_to_list,
        bcc=bcc_list)
    msg.attach_alternative(html_final, "text/html")
    
    return msg.send()