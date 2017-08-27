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