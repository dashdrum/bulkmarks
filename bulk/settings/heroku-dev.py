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
MIDDLEWARE.insert(2,'debug_toolbar.middleware.DebugToolbarMiddleware')

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

def custom_show_toolbar(request):
     return DEBUG  # Always show toolbar if DEBUG is True

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'bulk.settings.heroku-dev.custom_show_toolbar',
}

## end Django Debug Toolbar settings

## django-postgres-metrics settings

if DEBUG:
    INSTALLED_APPS.insert(0,'postgres_metrics.apps.PostgresMetrics')

''' Environment variables required

	DJANGO_SECRET_KEY - 50 char random string
	DJANGO_DEBUG - Set to '' for False
	DJANGO_ALLOWED_HOSTS - Omit for all hosts
	DJANGO_SETTINGS_MODULE - bulk.settings.heroku-dev
'''