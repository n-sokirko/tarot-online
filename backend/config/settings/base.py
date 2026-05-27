"""Base Django settings — extended by dev.py and prod.py."""
import os
from datetime import timedelta
from pathlib import Path

from decouple import Config, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env explicitly so values in the file always win, even when an empty
# env var has been injected into the process (some shells/harnesses do this,
# and decouple's default `config()` reads os.environ first which then
# silently overrides the .env value with an empty string).
# .env lives in the project root, one level above BASE_DIR (= backend/).
_ENV_FILE = BASE_DIR.parent / '.env'
if _ENV_FILE.exists():
    _repo = RepositoryEnv(str(_ENV_FILE))
    for _k, _v in _repo.data.items():
        # Override only when the existing env value is missing or empty.
        if not os.environ.get(_k):
            os.environ[_k] = _v
    config = Config(_repo)
else:
    from decouple import config  # noqa: F401  fallback to AutoConfig

SECRET_KEY = config('DJANGO_SECRET_KEY', default='dev-only-change-me')
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda s: s.split(',')
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    # local
    'apps.tarot',
    'apps.readings',
    'apps.users',
    'apps.billing',
    'apps.runes',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='tarot'),
        'USER': config('POSTGRES_USER', default='tarot'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='tarot'),
        'HOST': config('POSTGRES_HOST', default='localhost'),
        'PORT': config('POSTGRES_PORT', default='5432'),
    }
}

AUTH_USER_MODEL = 'users.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Tarot Online API',
    'VERSION': '0.1.0',
}

# Google OAuth
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')

# Anthropic
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')
ANTHROPIC_MODEL_FREE = config('ANTHROPIC_MODEL_FREE', default='claude-haiku-4-5-20251001')
ANTHROPIC_MODEL_PREMIUM = config('ANTHROPIC_MODEL_PREMIUM', default='claude-sonnet-4-6')
ANTHROPIC_MODEL_DEEP = config('ANTHROPIC_MODEL_DEEP', default='claude-opus-4-7')

# Paddle (Merchant of Record)
PADDLE_ENV = config('PADDLE_ENV', default='sandbox')  # sandbox | production
PADDLE_API_KEY = config('PADDLE_API_KEY', default='')
PADDLE_WEBHOOK_SECRET = config('PADDLE_WEBHOOK_SECRET', default='')
PADDLE_CLIENT_TOKEN = config('PADDLE_CLIENT_TOKEN', default='')  # public, fed to frontend

# Celery
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
