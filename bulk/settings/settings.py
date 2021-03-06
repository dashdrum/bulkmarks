"""
Django settings for bulk project.

Generated by 'django-admin startproject' using Django 1.11.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from os.path import join, abspath, dirname
from os import environ

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..')

DEBUG = bool(environ.get('DJANGO_DEBUG', False))

SECRET_KEY = environ.get('DJANGO_SECRET_KEY',None)

if DEBUG and not SECRET_KEY:
	SECRET_KEY = 'o-jhxtt-7f&$x6*yb8=cexcrn=3w0p(^7g3t%gl6tt*1d8ze5h'

ALLOWED_HOSTS = environ.get('DJANGO_ALLOWED_HOSTS',[])
if ALLOWED_HOSTS:
	ALLOWED_HOSTS = ALLOWED_HOSTS.split(',')
else:
	ALLOWED_HOSTS = ['*']

##INTERNAL_IPS = ('127.0.0.1',)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = ('bulk.backends.CaseInsensitiveModelBackend', )

SESSION_COOKIE_AGE = 86400 # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Application definition

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',

	'rest_framework',
	'widget_tweaks',
	'taggit',

	'profiles',
	'marketing',
	'bulk',
	'links',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bulk.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [join(BASE_DIR, 'bulk/templates').replace ('\\','/'),],
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

WSGI_APPLICATION = 'bulk.wsgi.application'




# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_L10N = False

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
	join(BASE_DIR, "bulk/static"),
)

if DEBUG:
	STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
else:
	STATIC_ROOT = environ['DJANGO_STATIC_ROOT']

## Whitenoise - Insert in 2nd place after SecurityMiddleware

MIDDLEWARE.insert(1,'whitenoise.middleware.WhiteNoiseMiddleware')

# Add app before django.contrib.staticfiles to enable Whitenoise in development

for i, app in enumerate(INSTALLED_APPS):
	if app == 'django.contrib.staticfiles':
		insert_point = i
INSTALLED_APPS.insert(insert_point,'whitenoise.runserver_nostatic')

# DRF Settings

REST_FRAMEWORK = {
	'DEFAULT_PERMISSION_CLASSES': (
		'rest_framework.permissions.AllowAny',
),
	'DEFAULT_AUTHENTICATION_CLASSES': (
		# 'rest_framework.authentication.BasicAuthentication',
		'rest_framework.authentication.SessionAuthentication',
	)

}

TAGGIT_CASE_INSENSITIVE = True

# Default is not to use Celery
USE_CELERY = False


#-----------------------------------------------------------------------------#
#
#    Heartbeat settings
#

INSTALLED_APPS += ('heartbeat',)

if 'heartbeat' in INSTALLED_APPS:
	HEARTBEAT = {
	  'package_name': 'bulk',
	  'checkers': [
		  'heartbeat.checkers.databases',  ## Will check the DB connection
	  ],
	  'auth': {'authorized_ips': ('127.0.0.1','10.0.0.0/8'),},
	}

#
#-----------------------------------------------------------------------------#



SENDGRID_API_KEY = environ.get('SENDGRID_API_KEY',None)

if SENDGRID_API_KEY:
	EMAIL_BACKEND = "sgbackend.SendGridBackend"
else:
	EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

