## Heroku development settings

from os import environ, path

import dj_database_url

from .settings import *


# Database

DATABASES = {
    'default': dj_database_url.config(
        default=environ.get('DATABASE_URL')
    )
}

## Heroku Whitenoise setting

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

STATIC_ROOT = path.join(BASE_DIR, 'staticfiles')

## Django Debug Toolbar settings

INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

## end Django Debug Toolbar settings

''' Environment variables required

	DJANGO_SECRET_KEY - 50 char random string
	DJANGO_DEBUG - Set to '' for False
	DJANGO_ALLOWED_HOSTS - Omit for all hosts
	DJANGO_SETTINGS_MODULE - bulk.settings.heroku-dev
'''