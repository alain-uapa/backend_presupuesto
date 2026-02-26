from django.db import models
from django.conf import settings

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group

@receiver(post_save, sender=User)
def asignar_grupo_colaborador(sender, instance, created, **kwargs):
    if created:
        # Buscamos el grupo (asegúrate de que el nombre sea exacto)
        grupo, _ = Group.objects.get_or_create(name='Colaborador')
        instance.groups.add(grupo)
        
class Sede(models.Model):
    codigo = models.CharField(max_length=3, unique=True)
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class CuentaAnalitica(models.Model):
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

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
    
    ubicacion = models.ForeignKey(Sede, on_delete=models.PROTECT)
    cuenta_analitica = models.ForeignKey(CuentaAnalitica, on_delete=models.PROTECT)
    
    presupuesto_pre_aprobado = models.DecimalField(max_digits=12, decimal_places=2)
    monto_a_ejecutar = models.DecimalField(max_digits=12, decimal_places=2)
    
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    confirmado = models.BooleanField(default=False, verbose_name="Confirmado")
    # Nombre más apropiado para el motivo de rechazo
    observaciones_supervisor = models.TextField(blank=True, null=True, verbose_name="Observaciones de Revisión")
  
    @property
    def get_nombre_colaborador(self):
        # get_full_name() es un método estándar de Django que une first_name y last_name
        return self.colaborador.get_full_name()
    
    def __str__(self):
        return f"{self.titulo} - {self.colaborador.get_full_name()}"

class AdjuntoSolicitud(models.Model):
    # Relación directa: Si se borra la solicitud, se borran las referencias de sus adjuntos
    solicitud = models.ForeignKey(
        SolicitudPresupuesto, 
        on_delete=models.CASCADE, 
        related_name='adjuntos'
    )
    
    # Campos de metadata y Drive
    nombre = models.CharField(max_length=255, verbose_name="Nombre del archivo")
    drive_id = models.CharField(max_length=255, unique=True)
    url_view = models.TextField(verbose_name="Enlace de visualización")
    mime_type = models.CharField(max_length=100, verbose_name="Tipo de archivo")
    es_certificado = models.BooleanField(default=False, verbose_name="Es certificado")
    aprobado = models.BooleanField(default=False, verbose_name="Aprobado en certificado")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.nombre} - Solicitud {self.solicitud_id}"

    class Meta:
        db_table = 'AdjuntoSolicitud'
        verbose_name = 'Adjunto de Solicitud'
        verbose_name_plural = 'Adjuntos de Solicitudes'

class Configuracion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    valor = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"

    @classmethod
    def get_value(cls, nombre, default=None):
        """
        Busca una configuración por nombre y devuelve su valor.
        Uso: Configuracion.get_value('GOOGLE_DRIVE_JSON')
        """
        config = cls.objects.filter(nombre=nombre).first()
        if config:
            return config.valor
        return default

    @classmethod
    def get_usuarios_compra_por_sede(cls, sede_codigo):
        """
        Busca una configuración de usuarios de contabilidad por código de sede.
        
        Args:
            sede_codigo: Código de la sede (ej: 'SED001', '01', etc.)
            
        Returns:
            El valor de la configuración si se encuentra, None en caso contrario.
        """
        # Buscar configuraciones que contengan 'USUARIOS_COMRRA_'
        # y que terminen con el código de sede
        config = cls.objects.filter(
            nombre__contains='USUARIOS_COMPRA_',
            nombre__endswith=sede_codigo
        ).first()
        
        if config:
            return config.valor
        return None

    def __str__(self):
        return self.nombre

class GoogleConfig(models.Model):
    nombre = models.CharField(max_length=100, default="Principal")
    # JSONField es ideal para guardar el contenido completo del archivo .json
    credentials_json = models.JSONField(help_text="Pega aquí el contenido completo del JSON de la Service Account")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class SecuenciaCertificado(models.Model):
    anno = models.IntegerField(unique=True)
    numero = models.IntegerField(default=0)

    class Meta:
        db_table = 'SecuenciaCertificado'
        verbose_name = 'Secuencia de Certificado'
        verbose_name_plural = 'Secuencias de Certificados'

    @classmethod
    def get_next_number(cls):
        from django.utils import timezone
        current_year = timezone.now().year
        
        secuencia, created = cls.objects.get_or_create(
            anno=current_year,
            defaults={'numero': 0}
        )
        
        return secuencia.numero + 1

    @classmethod
    def increment_sequence(cls):
        from django.utils import timezone
        current_year = timezone.now().year
        
        secuencia, created = cls.objects.get_or_create(
            anno=current_year,
            defaults={'numero': 0}
        )
        
        secuencia.numero += 1
        secuencia.save()
        
        return secuencia.numero

    def __str__(self):
        return f"Sequencia {self.anno}: {self.numero}"