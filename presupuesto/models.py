from django.db import models
from django.conf import settings

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

class CuentaAnalitica(models.Model):
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class SolicitudPresupuesto(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    TIPO_CHOICES = [
        ('DESEMBOLSO', 'Desembolso'),
        ('DESVIACION', 'Desviación'),
    ]
    
    RUBRO_CHOICES = [
        ('SERVICIOS', 'Gastos de servicios y suministros'),
        ('ACTIVIDADES', 'Plan de actividades'),
        ('INVERSION', 'Inversión'),
    ]

    # Relación con el Colaborador
    colaborador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    titulo = models.CharField(max_length=200, verbose_name="Nombre de la solicitud")
    descripcion = models.TextField()
    
    tipo_solicitud = models.CharField(max_length=20, choices=TIPO_CHOICES)
    rubro_presupuestal = models.CharField(max_length=20, choices=RUBRO_CHOICES)
    
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)
    cuenta_analitica = models.ForeignKey(CuentaAnalitica, on_delete=models.PROTECT)
    
    presupuesto_pre_aprobado = models.DecimalField(max_digits=12, decimal_places=2)
    monto_a_ejecutar = models.DecimalField(max_digits=12, decimal_places=2)
    
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    # Nombre más apropiado para el motivo de rechazo
    observaciones_supervisor = models.TextField(blank=True, null=True, verbose_name="Observaciones de Revisión")

    @property
    def get_nombre_colaborador(self):
        # get_full_name() es un método estándar de Django que une first_name y last_name
        return self.colaborador.get_full_name()
    
    def __str__(self):
        return f"{self.titulo} - {self.colaborador.get_full_name()}"