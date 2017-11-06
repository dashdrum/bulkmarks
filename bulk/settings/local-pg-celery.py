## Local development settings

from .settings import *


DEBUG = True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bulk',
        'USER': 'bulk',
        'PASSWORD': 'bulk',
        'HOST': 'localhost',
        'PORT': '',
    }
}

## Django Debug Toolbar settings

INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

## end Django Debug Toolbar settings

## Celery settings

INSTALLED_APPS += ('django_celery_results',)

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

## end  Celery settings
