from django.contrib import admin
from .models import DriveFolder, SolicitudPresupuesto, Sede, CuentaAnalitica, GoogleConfig, Configuracion, AdjuntoSolicitud, CuentaContable

@admin.register(SolicitudPresupuesto)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'colaborador', 'estado', 'fecha_solicitud', 'monto_a_ejecutar')
    list_filter = ('estado', 'tipo_solicitud', 'ubicacion')
    search_fields = ('titulo', 'colaborador__email')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si es superusuario o supervisor (puedes usar grupos), ve todo
        if request.user.is_superuser or request.user.groups.filter(name='Supervisor').exists():
            return qs
        # Si no, solo ve lo suyo
        return qs.filter(colaborador=request.user)

admin.site.register(Sede)
admin.site.register(CuentaAnalitica)
admin.site.register(GoogleConfig)
@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'valor', 'descripcion')


admin.site.register(AdjuntoSolicitud)
admin.site.register(CuentaContable)
admin.site.register(DriveFolder)