"""
Django settings for rcjaRegistration project.

Generated by 'django-admin startproject' using Django 2.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import environ
import sys
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = environ.Env(
    DEBUG=(bool, False),
    SENDGRID_API_KEY=(str, 'API_KEY'),
    ALLOWED_HOSTS=(list, ['127.0.0.1', 'localhost']),
    STATIC_ROOT=(str, os.path.join(BASE_DIR, "static")),
    USE_SQLLITE_DB=(bool, False),
    AWS_ACCESS_KEY_ID=(str, 'AWS_ACCESS_KEY_ID'),
    AWS_SECRET_ACCESS_KEY=(str, 'AWS_SECRET_ACCESS_KEY'),
    CMS_EVENT_URL_VIEW=(str, 'CMS_EVENT_URL'), # {EVENT_ID} will be replaced
    STATIC_BUCKET=(str, 'STATIC_BUCKET'),
    PUBLIC_BUCKET=(str, 'PUBLIC_BUCKET'),
    PRIVATE_BUCKET=(str, 'PRIVATE_BUCKET'),
    SENTRY_DSN = (str, 'SENTRY_DSN'),
    SENTRY_ENV = (str, 'production'),
    DEV_SETTINGS=(bool, False),
    DEFAULT_FROM_EMAIL=(str, 'entersupport@robocupjunior.org.au'),
    USE_PROXY=(bool, False),
    ENVIRONMENT=(str, 'development')
)

assert not (len(sys.argv) > 1 and sys.argv[1] == 'test'), "These settings should never be used to run tests"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

CORS_ALLOWED_ORIGINS = [
    "https://www.robocupjunior.org.au", # For public api
    "https://robocupjunior.org.au", # For public api
]

CSRF_TRUSTED_ORIGINS = []

DEV_SETTINGS = env('DEV_SETTINGS')

# Add the allowed hosts to cors
# https unless is the default local_hosts for dev
_allowed_hosts_list = env('ALLOWED_HOSTS') if isinstance(env('ALLOWED_HOSTS'), list) else [env('ALLOWED_HOSTS')]
_allowed_hosts_list = [f"https://{host}" for host in _allowed_hosts_list]
if DEV_SETTINGS:
    _allowed_hosts_list.append("http://127.0.0.1:8000")
    _allowed_hosts_list.append("http://localhost:8000")

CORS_ALLOWED_ORIGINS += _allowed_hosts_list
CSRF_TRUSTED_ORIGINS += _allowed_hosts_list

if env('USE_PROXY'):
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition

INSTALLED_APPS = [
    'users.apps.UsersConfig',
    'widget_tweaks',
    'userquestions.apps.UserquestionsConfig',
    'regions.apps.RegionsConfig',
    'coordination.apps.CoordinationConfig',
    'teams.apps.TeamsConfig',
    'events.apps.EventsConfig',
    'eventfiles.apps.EventfilesConfig',
    'invoices.apps.InvoicesConfig',
    'schools.apps.SchoolsConfig',
    'workshops.apps.WorkshopsConfig',
    'association.apps.AssociationConfig',
    'common.apps.CommonConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'axes',
    'storages',
    'corsheaders',
]

AUTH_USER_MODEL = 'users.User'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.redirectsMiddleware.RedirectMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'rcjaRegistration.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'common.globalContexts.yearsContext',
                'common.globalContexts.environmentContext',
            ],
        },
    },
]

WSGI_APPLICATION = 'rcjaRegistration.wsgi.application'

AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    'axes.backends.AxesBackend',

    # Django ModelBackend is the default authentication backend.
    'django.contrib.auth.backends.ModelBackend',
]

# Axes
# AXES_ONLY_USER_FAILURES = True
AXES_USERNAME_FORM_FIELD = 'email'
AXES_RESET_ON_SUCCESS = True
AXES_VERBOSE = False
AXES_IPWARE_META_PRECEDENCE_ORDER = [
   'HTTP_X_FORWARDED_FOR',
]
# 20 failed attempts results in hour long lockout
AXES_FAILURE_LIMIT = 20
AXES_COOLOFF_TIME = 1

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

if env('USE_SQLLITE_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': env.db(),
    }


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

if DEV_SETTINGS and DEBUG:
    AUTH_PASSWORD_VALIDATORS = []
else:
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'common.hibpValidator.PWNEDPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedSHA1PasswordHasher',
]

# HIBP settings

PWNED_VALIDATOR_ERROR = "Your password was determined to have been involved in a major security breach. This was not a breach of this site. This can be caused by using this password on a different site that was breached or if someone else used the same password. Go to https://haveibeenpwned.com/Passwords for more information."
PWNED_VALIDATOR_ERROR_FAIL = "We could not validate the safety of this password. This does not mean the password is invalid. Please try again in a little bit, if the problem persists please contact us."
PWNED_VALIDATOR_FAIL_SAFE = False

# Dev only
if DEV_SETTINGS:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PASSWORD_RESET_TIMEOUT_DAYS = 1 # 1 day
SESSION_COOKIE_AGE = 172800 # 2 days

# Email

SENDGRID_API_KEY = env('SENDGRID_API_KEY')

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True

SERVER_EMAIL = 'system@enter.robocupjunior.org.au'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# REST

DEFAULT_RENDERER_CLASSES = (
    'rest_framework.renderers.JSONRenderer',
)

if DEV_SETTINGS and DEBUG:
    DEFAULT_RENDERER_CLASSES = DEFAULT_RENDERER_CLASSES + (
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

REST_FRAMEWORK = {
    # 'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.OrderingFilter','rest_framework.filters.SearchFilter'),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        ),
    'DEFAULT_PERMISSION_CLASSES': ('common.apiPermissions.IsSuperUser',),
    'DEFAULT_RENDERER_CLASSES': DEFAULT_RENDERER_CLASSES,
    'DEFAULT_PAGINATION_CLASS': 'common.headerLinkPagination.LinkHeaderPagination',
    'PAGE_SIZE': 50
}


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-au'

TIME_ZONE = 'Australia/Melbourne'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

#https://stackoverflow.com/questions/44160666/valueerror-missing-staticfiles-manifest-entry-for-favicon-ico


LOGIN_REDIRECT_URL = '/'

# AWS SETTINGS

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_ACL = None

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# CMS SETTINGS

CMS_EVENT_URL_VIEW = env('CMS_EVENT_URL_VIEW')

# Static
STATIC_ROOT = env('STATIC_ROOT')
STATICFILES_DIRS = [os.path.join(BASE_DIR, "staticfiles")]

STATIC_BUCKET = env('STATIC_BUCKET')
STATIC_DOMAIN = f'{STATIC_BUCKET}.s3.amazonaws.com'

AWS_STATIC_LOCATION = ''

if STATIC_BUCKET != 'STATIC_BUCKET' and AWS_ACCESS_KEY_ID != 'AWS_ACCESS_KEY_ID':
    STATICFILES_STORAGE = 'rcjaRegistration.storageBackends.StaticStorage'
    STATIC_URL = f"https://{STATIC_DOMAIN}/{STATIC_BUCKET}/"
else:
    STATIC_URL = '/static/'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Public
PUBLIC_BUCKET = env('PUBLIC_BUCKET')
PUBLIC_DOMAIN = f'{PUBLIC_BUCKET}.s3.amazonaws.com'
AWS_PUBLIC_MEDIA_LOCATION = ''

# Private
PRIVATE_BUCKET = env('PRIVATE_BUCKET')
PRIVATE_DOMAIN = f'{PRIVATE_BUCKET}.s3.amazonaws.com'
AWS_PRIVATE_MEDIA_LOCATION = ''

DEFAULT_FILE_STORAGE = 'rcjaRegistration.storageBackends.PrivateMediaStorage'


SENTRY_DSN = env('SENTRY_DSN')
if SENTRY_DSN != 'SENTRY_DSN':
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env('SENTRY_ENV'),
        enable_tracing=False,
        sample_rate=1.0,
        send_default_pii=True,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=False,
                signals_spans=False,
                cache_spans=False,
            ),
        ]
    )

# Environment
ENVIRONMENT = env('ENVIRONMENT')
