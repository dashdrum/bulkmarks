## Example settings - copy and edit for each instance

## Set DJANGO_SETTINGS_MODULE to point to your edited file
##  eg. DJANGO_SETTINGS_MODULE=dupe.settings.devl

## Files that include passwords or other authentication information should NOT be included in DVCS

from .settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': '****',
        'HOST': '*******.***.***',
        'PORT': '****',
        'USER': '********',
        'PASSWORD': '********',
    }
}

## Any other instance specific settings here


## Django Debug Toolbar settings

#INSTALLED_APPS += ('debug_toolbar',)
#MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
#INTERNAL_IPS = ('127.0.0.1',)

## end Django Debug Toolbar settings
