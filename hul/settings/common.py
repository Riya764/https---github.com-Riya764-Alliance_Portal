'''Import sys (to adjust Python path)'''
from os.path import abspath, basename, dirname, join, normpath
import sys
import os
import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)


# Import some utility functions
# #########################################################
# Fetch Django's project directory
DJANGO_ROOT = dirname(dirname(abspath(__file__)))


# Fetch the project_root
PROJECT_ROOT = dirname(DJANGO_ROOT)
print(DJANGO_ROOT)
# Fetch the doc/tmp_root
TMP_ROOT = join(PROJECT_ROOT, 'doc', 'tmp')

environ.Env.read_env(os.path.join(PROJECT_ROOT, 'hul', '.env'))

# ##### SECURITY CONFIGURATION ############################
ALLOWED_HOSTS = ['*']
# We store the secret key here
# The required SECRET_KEY is fetched at the end of this file
SECRET_FILE = normpath(join(PROJECT_ROOT, 'run', 'SECRET.key'))


# Finally grab the SECRET KEY
try:
    # SECRET_KEY = env('SECRET_KEY')
    SECRET_KEY = 'fn!e-41hr(iwrzigjd4rya8psyu8v6ju=c(u2g%1wutydhx+n-'
except IOError:
    try:
        from django.utils.crypto import get_random_string
        CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789!$%&()=+-_'
        SECRET_KEY = get_random_string(50, CHARS)
        with open(SECRET_FILE, 'w') as f:
            f.write(SECRET_KEY)
    except IOError:
        raise Exception('Could not open %s for writing!' % SECRET_FILE)
# ##### PATH CONFIGURATION ################################


# The name of the whole site
SITE_NAME = basename(DJANGO_ROOT)

# Collect static files here
#STATIC_ROOT = join(PROJECT_ROOT, 'run', 'static')
STATIC_ROOT = '/data/hul/run/static/admin/'

# Collect media files here
MEDIA_ROOT = join(PROJECT_ROOT, 'run', 'media')

# look for static assets here
STATICFILES_DIRS = [
    join(PROJECT_ROOT, 'static'),
]
# look for templates here
# This is an internal setting, used in the TEMPLATES directive
PROJECT_TEMPLATES = [
    join(PROJECT_ROOT, 'templates'),
]

# Add apps/ to the Python path
sys.path.append(normpath(join(PROJECT_ROOT, 'apps')))


SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_BROWSER_XSS_FILTER = True

CORS_ORIGIN_ALLOW_ALL = True

X_FRAME_OPTIONS = 'AllowAny'

SESSION_COOKIE_HTTPONLY = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_BROWSER_XSS_FILTER = True

# CSRF_COOKIE_HTTPONLY = True

HttpOnly = True


# ##### APPLICATION CONFIGURATION #########################

# This are the apps
DJANGO_APPS = (
    'admin_view_permission',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oauth2_provider',
    'rest_framework',
)

THIRD_PARTY_APPS = (
    'rangefilter',
    'corsheaders',
    'tinymce',
    'easy_pdf',
    's3direct',
    'djcelery',
    # 'debug_toolbar',
    'import_export',
    'django_admin_listfilter_dropdown',
    'celery_progress',
)

LOCAL_APPS = (
    'app',
    'log',
    'job',
    'cms',
    'product',
    'localization',
    'orders',
    'offers',
    'claim',
    'pdp',
    'misreporting',
    'master',
    'moc'
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middlewares
MIDDLEWARE_CLASSES = (
    'hul.custom_middleware.LoggingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)
# Template stuff
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': PROJECT_TEMPLATES,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'hul.context_processors.getstockist',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'hul.exceptions.custom_exception_handler'
}

# These persons receive error notification
ADMINS = (
    ('Mayank', 'mayank.kukreja@netsolutions.com'),
    ('Prasenjit', 'prasenjit.jha@netsolutions.com'),
)

MANAGERS = ADMINS

AUTH_USER_MODEL = 'app.User'

ADMIN_PAGE_SIZE = 20

CANCEL_BEFORE = 30
# ##### DJANGO RUNNING CONFIGURATION ######################

# The default WSGI application
WSGI_APPLICATION = '%s.wsgi.application' % SITE_NAME

# The root URL configuration
ROOT_URLCONF = '%s.urls' % SITE_NAME

# This site's ID
SITE_ID = 1

# The URL for static files
STATIC_URL = '/static/'

# The URL for media files
MEDIA_URL = '/media/'


EXPORT_PATH = join(PROJECT_ROOT, "run", "export")

# ##### INTERNATIONALIZATION ##############################

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

# Internationalization
USE_I18N = True

# Localisation
USE_L10N = False

# date time format
DATETIME_FORMAT = 'd M y'
DATETIME_FORMAT_CSV = '%d/%m/%y'

# enable timezone awareness by default
USE_TZ = True

LST_APP_FOR_LOGGING = ['app', 'products', 'orders']

ADMIN_SITE_HEADER = 'Hindustan Unilever'

ADMIN_SITE_TITLE = 'Hindustan Unilever'

APPLICATION_NAME = 'HUL-MOBILAPP'

OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'

S3DIRECT_DESTINATIONS = {
    'category_images': {
        'key': 'category_images',
        'allowed': ['image/jpeg', 'image/png'],
        'content_length_range': (5000, 20000000),
    },
    'product_images': {
        'key': 'product_images',
        'allowed': ['image/jpeg', 'image/png'],
        'content_length_range': (5000, 20000000),
    },
    'user_images': {
        'key': 'user_images',
        'allowed': ['image/jpeg', 'image/png'],
        'content_length_range': (5000, 20000000),
    },
}


# # Add logging to the app to make debugging / monitoring easier
#
# ##
# # Django-Splunk-Logging
# # #
# # Enable or disable Splunk Logs
# # SPLUNK_LOGS = True
# # # HTTP Event Collector Token
# # SPLUNK_TOKEN = "4970a69e-ce6d-4334-8044-1894df1696bc"
# # # Splunk Event Collector has enabled HTTPS
# # SPLUNK_HTTPS = False
# # # Splunk Server Address
# # SPLUNK_ADDRESS = "localhost"
# # # Event Collector Port (default: 8088)
# # SPLUNK_EVENT_COLLECTOR_PORT = "8088"
# # # Enable threading on event sending
# # SPLUNK_THREAD_EVENTS = True
#
# LOG_FILE_PATH = join(PROJECT_ROOT, 'hul.log')
# GUARD_APP_LOGGING = True
#
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'filename': LOG_FILE_PATH,
#         },
#         # 'splunk':{
#         #     'class':'django_splunk_logging.SplunkHandler'
#         # },
#     },
#     'loggers': {
#         'hul': {
#             'handlers': ['file'],
#             'level': 'DEBUG',
#             'propagate': True,
#         }
#     }
# }
