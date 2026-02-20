# Configuración de Logging

## Descripción

Este proyecto utiliza el módulo de logging de Python integrado con Django para registrar errores del servidor.

## Ubicación

- **Directorio de logs**: `presupuesto/logs/`
- **Archivo principal**: `errors.log`

## Configuración Actual

La configuración está definida en `core/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'formatter': 'verbose',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### Componentes

| Componente | Descripción |
|------------|-------------|
| **version** | Versión del esquema de configuración (1) |
| **disable_existing_loggers** | False para no desactivar loggers existentes |
| **formatters** | Define el formato de salida |
| **handlers** | Define dónde se envían los logs |

### Handler de Archivo

- **Clase**: `TimedRotatingFileHandler` - rota archivos basado en tiempo
- **Nivel**: `ERROR` - solo captura errores y superiores
- **when**: `midnight` - rota a medianoche (00:00)
- **interval**: `1` - rota cada 1 día
- **backupCount**: `7` - mantiene 7 archivos de respaldo

### Formatter

- **Formato**: `{levelname} {asctime} {module} {message}`
- **Ejemplo**: `ERROR 2026-02-20 10:30:45,123 solicitudes_view Exception: ...`

## Rotación de Archivos

### Cómo funciona

1. **Rotación diaria**: A medianoche, `errors.log` se renombra a `errors.log.2026-02-20`
2. **Nuevo archivo**: Se crea un nuevo `errors.log` vacío
3. **Respaldo**: Se mantienen hasta 7 archivos de respaldo (7 días)

### Archivos generados

```
logs/
├── errors.log          # Log actual (hoy)
├── errors.log.2026-02-19  # Ayer
├── errors.log.2026-02-18  # 2 días atrás
├── ...
└── errors.log.2026-02-13  # 7 días atrás (más antiguo)
```

### Limpieza automática

Los archivos mayores a 7 días se eliminan automáticamente.

## Uso en Código

### Función helper

El proyecto incluye una utilidad en `core/utils/logging.py`:

```python
from core.utils.logging import log_error

def tu_view(request):
    try:
        # tu código
        pass
    except Exception as e:
        log_error(request, e, {'funcion': 'tu_view'})
        return JsonResponse({"error": str(e)}, status=400)
```

### Función helper + respuesta JSON

```python
from core.utils.logging import error_json_response

def tu_view(request):
    try:
        # tu código
        pass
    except Exception as e:
        return error_json_response(e, "Mensaje de error personalizado")
```

### Información registrada

Cada error incluye:

- **Nivel**: ERROR
- **Timestamp**: Fecha y hora del error
- **Módulo**: Archivo donde ocurrió el error
- **Mensaje**: Descripción del error + traceback completo
- **Extra**:
  - `request_method`: GET, POST, etc.
  - `request_path`: URL de la petición
  - `user`: Información del usuario (username, email)

## Ver logs en tiempo real

```bash
# Ver el archivo actual
tail -f logs/errors.log

# Ver últimos 50 líneas
tail -n 50 logs/errors.log
```

## Cambiar configuración

### Rotar por tamaño en lugar de tiempo

Cambiar el handler:

```python
'class': 'logging.handlers.RotatingFileHandler',
'maxBytes': 10 * 1024 * 1024,  # 10 MB
'backupCount': 5,
```

### Cambiar nivel de logging

```python
'level': 'DEBUG',  # Captura todo
# o
'level': 'WARNING',  # Solo warnings y errores
```

### Agregar más loggers

```python
'loggers': {
    'django': {...},
    'presupuesto': {  # Agregar logger específico de app
        'handlers': ['file', 'console'],
        'level': 'ERROR',
    },
}
```
