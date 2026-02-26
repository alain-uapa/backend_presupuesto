EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'alainperez@uapa.edu.do'
EMAIL_HOST_PASSWORD = 'FjnFy4Ev@2025' 
DEFAULT_FROM_EMAIL = 'Solicitud de Presupuesto'

# Imprimir en la terminal
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'