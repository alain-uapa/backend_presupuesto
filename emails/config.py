EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'alainperez@uapa.edu.do'
EMAIL_HOST_PASSWORD = 'alqc rdyp gbzf wrbr' #Código de App password 
DEFAULT_FROM_EMAIL = 'Solicitud de Presupuesto'

# Imprimir en la terminal
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

"""
Crear contraseña de aplicación para usarla como host
Entra a tu cuenta de Google: Ve a myaccount.google.com.

Seguridad: En el menú de la izquierda, haz clic en Seguridad.

Verificación en 2 pasos: Asegúrate de que esté Activada. Si no, actívala.

Contraseñas de aplicaciones: Al final de la sección "Cómo inicias sesión en Google", busca la opción Contraseñas de aplicaciones (App Passwords).

Nota: Si no la encuentras, usa el buscador de la parte superior y escribe "Contraseñas de aplicaciones".

Crear: Ponle un nombre para identificarla (ej: "Sistema Presupuesto UAPA") y dale a Crear.

Copia el código: Te dará un código de 16 caracteres
"""