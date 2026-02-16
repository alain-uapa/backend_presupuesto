from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import SolicitudPresupuesto

class MisSolicitudesView(LoginRequiredMixin, ListView):
    model = SolicitudPresupuesto
    template_name = 'presupuesto/mis_solicitudes.html'
    context_object_name = 'solicitudes'

    def get_queryset(self):
        # Filtro estricto: solo lo que pertenece al usuario logueado
        return SolicitudPresupuesto.objects.filter(colaborador=self.request.user).order_by('-fecha_solicitud')