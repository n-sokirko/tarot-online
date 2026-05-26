from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', default='', cast=lambda s: [o for o in s.split(',') if o]
)
