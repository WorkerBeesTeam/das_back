import environ

project_root = environ.Path(__file__) - 3  
env = environ.Env(DEBUG=(bool, False),)  

CURRENT_ENV = 'dev' # 'dev' is the default environment
import builtins
if hasattr(builtins, "CURRENT_ENV"):
    CURRENT_ENV = builtins.CURRENT_ENV

# read the .env file associated with the settings that're loaded
env.read_env('{0}/das/{1}.env'.format(project_root, CURRENT_ENV))

UPDATE_ACCEPTED_LIST=env('UPDATE_ACCEPTED_LIST')

FRONTEND_ROOT = env('FRONTEND_ROOT')
if not FRONTEND_ROOT.startswith('/'):
    FRONTEND_ROOT = str(environ.Path("{0}/{1}".format(project_root, FRONTEND_ROOT)))

ALLOWED_HOSTS = ['*']

#LANGUAGE_CODE = 'en-us'
#TIME_ZONE = 'Asia/Novosibirsk'
#USE_TZ = True
#USE_I18N = True
#USE_L10N = True

DATABASES = {
    'default': env.db()
}

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Django Packages
    'django_filters',
    'rest_framework',
    #'rest_framework_filters',
    'das',
#
#    'applications.scheme',
#    'applications.scheme_list'
]

ROOT_URLCONF = 'das.urls'

STATIC_URL = '/static/'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
STATICFILES_DIRS = [
    FRONTEND_ROOT
]

MEDIA_ROOT = FRONTEND_ROOT

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_ROOT, project_root + '/das/templates'],
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

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
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

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.DjangoModelPermissions',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 35,
}

import datetime
JWT_AUTH = {
    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'das.auth.jwt_response_payload_handler',
    'JWT_PAYLOAD_HANDLER':
        'das.auth.jwt_payload_handler',
    'JWT_ALLOW_REFRESH': True,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=900),
}

CSRF_COOKIE_SECURE=False

AUTH_USER_MODEL = 'das.User'

WSGI_APPLICATION = 'das.wsgi.application'

