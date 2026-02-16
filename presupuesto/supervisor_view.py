from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from .models import SolicitudPresupuesto

class PanelSupervisorView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SolicitudPresupuesto
    template_name = 'presupuesto/panel_supervisor.html'
    context_object_name = 'solicitudes'

    def test_func(self):
        # Solo permite el acceso si el usuario es superusuario 
        # o pertenece al grupo 'Supervisor'
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Supervisor').exists()

    def get_queryset(self):
        # El supervisor ve TODO, pero ponemos las PENDIENTES primero
        return SolicitudPresupuesto.objects.all().order_by('estado', '-fecha_solicitud')