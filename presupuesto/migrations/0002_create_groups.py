from django.db import migrations

def create_initial_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Supervisor')
    Group.objects.get_or_create(name='Colaborador')

class Migration(migrations.Migration):
    dependencies = [
        ('presupuesto', '0001_initial'), # El nombre de tu migración anterior
    ]
    operations = [
        migrations.RunPython(create_initial_groups),
    ]