from django.contrib import admin
from django.urls import path
from presupuesto import solicitudes_view as view
from presupuesto.catalogo import *
urlpatterns = [
    path("solicitudes/list", view.solicitudes_list, name='solicitudes_list'),  
    path('solicitudes/crear/', view.crear_solicitud, name='solicitudes_crear'),
    path('solicitudes/editar/<int:pk>/', view.editar_solicitud, name='solicitudes_editar'),
    path('solicitudes/status/<int:pk>/', view.cambiar_estado, name='cambiar_estado'),
    path('solicitudes/delete/<int:pk>/', view.eliminar_solicitud, name='eliminar_solicitud'),
    path('solicitudes/delete_attachment/<int:pk>/', view.eliminar_adjunto, name='eliminar_adjunto'),
    path('solicitudes/certificado/upload/<int:pk>/', view.upload_certificado, name='subir certificado'),
    path('ubicaciones/list/', ubicaciones_list, name='ubicaciones-list'),
    path('cuentas-analiticas/list/', cuentas_analiticas_list, name='cuentas-list'),  
]