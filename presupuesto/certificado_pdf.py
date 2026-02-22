from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.core.files.base import ContentFile
from weasyprint import HTML
from core.utils.logging import log_error
from .models import SolicitudPresupuesto, Configuracion
from .google_drive import upload_to_drive
from datetime import datetime

def get_certificado_template(request, pk):
    solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)              
    fecha_aprobacion = datetime.now().strftime('%d/%m/%Y')
    #submit_url = request.build_absolute_uri(reverse('certificado_create', args=[pk]))
    return render(request, 'presupuesto/certificado_template.html', {
        'centro_costo': "",
        'cuenta_utilizar': "",
        'sequence_number': '0001',
        'monto': solicitud.monto_a_ejecutar,
        'solicitante': solicitud.colaborador.get_full_name(),
        'rubro_presupuestal': solicitud.rubro_presupuestal,
        'fecha_solicitud': solicitud.fecha_solicitud.strftime('%d/%m/%Y') if solicitud.fecha_solicitud else '',
        'fecha_aprobacion': fecha_aprobacion,
        #'submit_url': submit_url,
    })
@csrf_exempt
def generar_certificado_pdf(request, pk):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)
        data = request.POST 
        
        pdf_file = generate_pdf('presupuesto/certificado_template.html', {
            'centro_costo': data.get('centro_costo'),
            'cuenta_utilizar': data.get('cuenta_utilizar'),
            'sequence_number': '0001',
            'monto': solicitud.monto_a_ejecutar,
            'solicitante': solicitud.colaborador.get_full_name(),
            'fecha_aprobacion': datetime.now().strftime('%d/%m/%Y')
        }, f"certificacion_{pk}")   
        
        archivo_drive = ContentFile(pdf_file, name=f"certificacion_{pk}.pdf")
        
        ID_FOLDER_DRIVE = Configuracion.get_value('ID_FOLDER_DRIVE')
        if not ID_FOLDER_DRIVE:
            raise ValueError("ID_FOLDER_DRIVE no configurado")
        
        resultado_drive = upload_to_drive(archivo_drive, ID_FOLDER_DRIVE, mimetype='application/pdf')
        
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