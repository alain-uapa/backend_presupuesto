from django.db import migrations

def cargar_cuentas_contables(apps, schema_editor):
    CuentaContable = apps.get_model('presupuesto', 'CuentaContable')
    
    cuentas = [
        ("1301", "TERRENOS"),
        ("1302", "EDIFICACIONES"),
        ("1303", "MOBILIARIO y EQUIPOS"),
        ("1304", "EQUIPOS DE TRANSPORTE"),
        ("1305", "EQUIPOS INFORMÁTICA Y COMUNICACIÓN"),
        ("1306", "MAQUINARIAS Y EQUIPOS DE MANTENIMIENTO"),
        ("1307", "FONDO BIBLIOGRÁFICO"),
        ("1308", "BIENES CULTURALES"),
        ("1309", "CONSTRUCCION EN PROCESO"),
        ("1310", "TRAJES ACADÉMICOS"),
        ("1311", "MAQUINARIA Y EQUIPOS PESADOS"),
        ("1401", "DERECHOS DE AUTOR MATERIAL DIDÁCTICO"),
        ("1402", "LICENCIAS SOFTWARES"),
        ("5102-05", "BENEFICIOS COMPLEMENTARIOS AL PERSONAL DOCENTE"),
        ("5102-02", "CAPACITACIÓN DEL PERSONAL DOCENTE"),
        ("5102-03", "UNIFORMES A CARGO DE UAPA PD"),
        ("5102-04", "INCENTIVOS Y RECONOCIMIENTOS AL PD"),
        ("5102-05-ALT", "DIETAS Y VIATICOS AL PA"), # Nota: Evitando duplicado exacto si el modelo es unique
        ("5102-06", "DIETAS Y VIATICOS P. INCAPRE"),
        ("5102-07", "ATENCION PERSONAL DOCENTE SIN NCF"),
        ("5102-08", "DIETAS Y VIATICOS DOC. SIN NCF"),
        ("5102-09", "GASTOS DE REPRESENTACION DOC. SIN NCF"),
        ("5102-05-99", "OTROS BENEFICIOS COMPLEMENTARIOS AL PD"),
        ("5102-05-10", "DIETAS Y VIATICOS DOCENTE"),
        ("5102-07-ALT", "ATENCION PERSONAL DOCENTE"),
        ("5102-14-02", "DIETAS Y VIATICOS PA"),
        ("5210-03", "ATENCIONES VISITANTES"),
        ("5210-05", "ATENCIONES A PARTICIPANTES"),
        ("2199-04", "FONDOS DE PROYECTOS"),
        ("5201-05-02", "CAPACITACIÓN PERSONAL ADM"),
        ("5201-05-03", "UNIFORMES A CARGO DE UAPA PADM"),
        ("5201-05-04", "INCENTIVOS Y RECONOCIMIENTOS AL PADM"),
        ("5201-05-05", "DIETAS Y VIATICOS PADM"),
        ("5201-05-06", "DIETAS Y VIATICOS ADM SIN NCF"),
        ("5201-05-07", "ATENCION PERSONAL ADM. SIN NCF"),
        ("5201-05-09", "DONACIONES SIN NCF"),
        ("5201-05-10", "GASTOS DE REPRESENTACION ADM SIN NCF"),
        ("5201-05-99", "OTROS BENEFICIOS COMPLEMENTARIOS AL PADM"),
        ("5201-06", "GASTOS DE REPRESENTACIÓN DEL PADM"),
        ("5201-07", "ATENCION PADM"),
        ("5201-08", "DONACIONES"),
        ("5210", "GASTOS REUNIONES Y EVENTOS"),
        ("5210-01", "CURSOS, SEMINARIOS Y CONGRESOS"),
        ("5210-02", "GRADUACIONES"),
        ("5210-04", "GASTOS FERIAS Y EVENTOS"),
        ("5202-01", "MATERIAL DE OFICINA"),
        ("5202-02", "MATERIAL MANTENIMIENTO"),
        ("5202-03", "MATERIAL DE PROMOCION Y DIFUSION"),
        ("5202-04", "COMBUSTIBLES Y LUBRICANTES"),
        ("5202-05", "MATERIAL CONSERJERIA"),
        ("5202-06", "GASTOS DE MATERIALES CONSTRUCCION"),
        ("5202-07", "MATERIALES DE JARDINERIA"),
        ("5202-08", "MATERIALES DE JARDINERIA SIN NCF"),
        ("5202-99", "OTROS GASTOS DE MATERIALES"),
        ("5203-04-01", "REP. MANT. EDIFICACIONES"),
        ("5203-04-02", "REP. MANT. MAQUINARIAS Y EQUIPOS"),
        ("5203-04-03", "REP. MANT. EQUIPOS TRANSPORTE"),
        ("5203-04-04", "REP. MANT. MOBILIARIOS"),
        ("5203-04-05", "REP. MANT. LIBROS DE BIBLIOTECA"),
        ("5203-04-06", "REPARACIONES Y MANTENIMIENTOS SIN NCF"),
        ("5203-05-01", "AUDITORIA"),
        ("5203-05-02", "CONSULTORIA ADMINISTRATIVA"),
        ("5203-05-03", "MERCADEO"),
        ("5203-05-06", "DOCTORA DISPENSARIO MEDICO"),
        ("5203-05-04", "CONSULTORIA LEGAL"),
        ("5203-05-05", "SERVICIOS TECNOLOGICOS"),
        ("5203-05-07", "SERVICIOS DE SEGURIDAD"),
        ("5203-05-08", "INVESTIGACION"),
        ("5203-05-09", "HONORARIOS PROFESIONALES SIN NCF"),
        ("5203-05-10", "CONSULTORIA LEGAL SIN NCF"),
        ("5203-11", "CUOTAS Y SUSCRIPCIONES"),
        ("5203-12", "FUMIGACION"),
        ("5203-13", "SERVICIOS DE LAVANDERIA"),
        ("5203-09", "PASAJES"),
        ("5203-99", "OTROS SERVICIOS EXTERNOS"),
        ("5204", "GASTOS PUBLICITARIOS"),
    ]

    for codigo, nombre in cuentas:
        CuentaContable.objects.get_or_create(codigo=codigo, defaults={'nombre': nombre})

class Migration(migrations.Migration):

    dependencies = [
        ('presupuesto', '0014_cuentacontable_solicitudpresupuesto_cuenta_contable'), # Reemplaza con la migración anterior
    ]

    operations = [
        migrations.RunPython(cargar_cuentas_contables),
    ]