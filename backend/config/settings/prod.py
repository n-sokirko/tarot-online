from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# TLS terminates before Django: at the Cloudflare edge (docker-compose, then
# plain HTTP to nginx) or at Railway's edge. We must NOT redirect HTTP→HTTPS
# internally (Django would loop). Instead, trust X-Forwarded-Proto, which both
# nginx and Railway set.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Railway has no nginx in front of Django, so WhiteNoise serves /static/ (admin,
# DRF). Behind nginx in docker-compose it is a no-op: nginx answers /static/
# from the shared volume before the request ever reaches Django.
_security = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')  # noqa: F405
MIDDLEWARE = [  # noqa: F405
    *MIDDLEWARE[:_security + 1],  # noqa: F405
    'whitenoise.middleware.WhiteNoiseMiddleware',
    *MIDDLEWARE[_security + 1:],  # noqa: F405
]
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS', default='', cast=lambda s: [o for o in s.split(',') if o]
)

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', default='', cast=lambda s: [o for o in s.split(',') if o]
)

# Allow both http:// and https:// for the same domain so that mobile browsers
# that follow an HTTP link (before Cloudflare upgrades it) are not blocked.
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https?://sokirdon\.com$',
    r'^https?://www\.sokirdon\.com$',
]
