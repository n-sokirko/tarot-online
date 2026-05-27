"""Test settings — uses SQLite in-memory so no external DB is needed."""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Speed up tests by using a weak hasher
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Suppress Django's debug log handler that tries to render templates
# (fails on Python 3.14 due to super() in template context __copy__)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Stub credentials for tests (override in individual tests via settings fixture)
TELEGRAM_BOT_TOKEN = 'test_bot_token:STUB'
TELEGRAM_PAYMENT_SECRET = 'a' * 64
TELEGRAM_BOT_USERNAME = 'test_bot'
