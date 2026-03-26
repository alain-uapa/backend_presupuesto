from django.db import migrations

def create_compra_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Compra RSS')
    Group.objects.get_or_create(name='Compra RSD')
    Group.objects.get_or_create(name='Compra RCO')

class Migration(migrations.Migration):
    dependencies = [
        ('presupuesto', '0024_rename_comentario_to_revision'),
    ]
    operations = [
        migrations.RunPython(create_compra_groups),
    ]
