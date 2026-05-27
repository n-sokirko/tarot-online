from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Cloudflare Tunnel terminates TLS at the edge and forwards plain HTTP to
# nginx.  We must NOT redirect HTTP→HTTPS internally (Django would loop).
# Instead, trust the X-Forwarded-Proto header that nginx injects.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS', default='', cast=lambda s: [o for o in s.split(',') if o]
)

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', default='', cast=lambda s: [o for o in s.split(',') if o]
)
