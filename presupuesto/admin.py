from django.contrib import admin
from .models import SolicitudPresupuesto, Ubicacion, CuentaAnalitica, GoogleConfig, Configuracion

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

admin.site.register(Ubicacion)
admin.site.register(CuentaAnalitica)
admin.site.register(GoogleConfig)
admin.site.register(Configuracion)