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
    'SHOW_TOOLBAR_CALLBACK': 'bulk.settings.local_pg.custom_show_toolbar',
}

## end Django Debug Toolbar settings




## django-postgres-metrics settings

if DEBUG:
    INSTALLED_APPS.insert(0,'postgres_metrics.apps.PostgresMetrics')
