"""
Configurações para rodar em rede interna (intranet), sem HTTPS.
Uso: DJANGO_SETTINGS_MODULE=config.settings.lan
"""

from decouple import Csv, config

from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=Csv())

# Rede interna sem certificado: NÃO forçar HTTPS nem cookies "secure"
# (senão o navegador não envia cookies/CSRF e o login quebra).
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
