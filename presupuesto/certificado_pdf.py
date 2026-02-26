from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.core.files.base import ContentFile
from weasyprint import HTML
from core.utils.logging import log_error
from .models import SolicitudPresupuesto, Configuracion, AdjuntoSolicitud, SecuenciaCertificado, CuentaContable
from .google_drive import upload_to_drive
from datetime import datetime
import json
from .utils import enviar_email_a_compras

def get_certificado_template(request, pk):
    solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)              
    fecha_aprobacion = datetime.now().strftime('%d/%m/%Y')
    sequence_number = SecuenciaCertificado.get_next_number()
    sequence_formatted = f"{sequence_number:04d}"
    cuenta_contable = request.GET.get('cuenta_contable', "")
    return render(request, 'presupuesto/certificado_template.html', {
        'cuenta_analitica': solicitud.cuenta_analitica,
        'cuenta_contable': cuenta_contable,
        'sequence_number': sequence_formatted,
        'monto': solicitud.monto_a_ejecutar,
        'solicitante': solicitud.colaborador.get_full_name(),
        'rubro_presupuestal': solicitud.rubro_presupuestal,
        'fecha_solicitud': solicitud.fecha_solicitud.strftime('%d/%m/%Y') if solicitud.fecha_solicitud else '',
        'fecha_aprobacion': fecha_aprobacion,
        'aprobado_por': request.user.get_full_name()
        #'submit_url': submit_url,
    })
@csrf_exempt
def generar_certificado_pdf(request, pk):
        
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)
        data = request.POST 
        
        cuenta_contable_id = data.get('cuenta_contable')
        if cuenta_contable_id:
            solicitud.cuenta_contable = cuenta_contable_id
            solicitud.save(update_fields=['cuenta_contable_id'])
        
        context = {
            'centro_costo': data.get('centro_costo'),
            'cuenta_analitica': solicitud.cuenta_analitica,
            'cuenta_contable': cuenta_contable_id,
            'sequence_number': data.get('sequence_number'),
            'rubro_presupuestal': solicitud.rubro_presupuestal,
            'monto': solicitud.monto_a_ejecutar,
            'solicitante': solicitud.colaborador.get_full_name(),
            'fecha_solicitud' : solicitud.fecha_solicitud.strftime('%d/%m/%Y'),
            'fecha_aprobacion': datetime.now().strftime('%d/%m/%Y'),
            'aprobado_por': request.user.get_full_name()
        }
        pdf_file = generate_pdf('presupuesto/certificado_template.html', context, f"certificacion_{pk}")   
        
        archivo_drive = ContentFile(pdf_file, name=f"certificacion_{pk}.pdf")
        
        ID_FOLDER_DRIVE = Configuracion.get_value('ID_FOLDER_DRIVE')
        if not ID_FOLDER_DRIVE:
            raise ValueError("ID_FOLDER_DRIVE no configurado")
        
        resultado_drive = upload_to_drive(archivo_drive, ID_FOLDER_DRIVE, mimetype='application/pdf')
        
        AdjuntoSolicitud.objects.create(
            solicitud=solicitud,
            nombre=f"certificacion_{pk}.pdf",
            drive_id=resultado_drive['id'],
            url_view=resultado_drive['webViewLink'],
            mime_type='application/pdf',
            es_certificado=True
        )
        
        adjuntos_ids = request.POST.getlist('attachment_ids')
        if adjuntos_ids:
            ids = json.loads(adjuntos_ids[0]) if isinstance(adjuntos_ids[0], str) else adjuntos_ids
            AdjuntoSolicitud.objects.filter(
                id__in=ids, 
                solicitud=solicitud
            ).update(aprobado=True)
        
        SecuenciaCertificado.increment_sequence()

        enviar_email_a_compras(request, solicitud)
        return JsonResponse({
            'drive_id': resultado_drive['id'],
            'url_view': resultado_drive['webViewLink']
        })
    except Exception as e:
        log_error(request, e, {'funcion': 'generar_certificado_pdf'})
        return JsonResponse({"error": str(e)}, status=400)
    
def generate_pdf(template, context, filename):
    html_string = render_to_string(template, context)    
    base_url = getattr(settings, 'BASE_URL', '')
    pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()
    return pdf_file