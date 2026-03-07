from django.db import migrations

def crear_configuraciones_iniciales(apps, schema_editor):
    # Usamos apps.get_model para evitar importar el modelo directamente
    Configuracion = apps.get_model('presupuesto', 'Configuracion')
    
    configuraciones = [
        {
            "nombre": "USUARIOS_COMPRA_RCO",
            "valor": "",
            "descripcion": "Correos que recibirán las notificaciones de los Certificados de Presupuesto de la Sede Nagua. Separados por ( ; )"
        },
        {
            "nombre": "USUARIOS_COMPRA_RSS",
            "valor": "",
            "descripcion": "Correos que recibirán las notificaciones de los Certificados de Presupuesto de la Sede Santiago. Separados por ( ; )"
        },
        {
            "nombre": "USUARIOS_COMPRA_RSD",
            "valor": "",
            "descripcion": "Correos que recibirán las notificaciones de los Certificados de Presupuesto de la Sede Santo Domingo. Separados por ( ; )"
        },
        {
            "nombre": "CORREOS_NUEVAS_SOLICITUDES",
            "valor": "",
            "descripcion": "Usuarios que recibirán el correo de nuevas solicitudes. Multiples valores separadors por ( ; )"
        },
        {
            "nombre": "ID_FOLDER_DRIVE",
            "valor": "1ponSLA7ARBpaQMvtPJP2x9v6ASXkNsi3",
            "descripcion": "Carpeta Compartida de Google Drive"
        },
    ]

    for data in configuraciones:
        # get_or_create evita errores si la migración se corre dos veces
        Configuracion.objects.get_or_create(
            nombre=data["nombre"],
            defaults={
                "valor": data["valor"],
                "descripcion": data["descripcion"]
            }
        )

class Migration(migrations.Migration):

    dependencies = [
        ('presupuesto', '0017_drivefolder'), # Esto se llena solo al crear la migración
    ]

    operations = [
        migrations.RunPython(crear_configuraciones_iniciales),
    ]