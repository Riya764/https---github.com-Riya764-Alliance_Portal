# Fetch our common settings
# import djcelery
from .common import *
# #########################################################

# ##### DEBUG CONFIGURATION ###############################
DEBUG =True
ADMINS = (
    ('Raghavendran', 'raghavendran.m@simtechitsolutions.com'),
    ('Shirish', 'shrishchandra.shukla@simtechitsolutions.com')
)

# ##### DATABASE CONFIGURATION ############################
# DATABASES = {
#     'default': env.db_url()
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hul11',                      
        'USER': 'postgres',
        'PASSWORD': '12345',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}




# EMAIL_DEFAULT = env('EMAIL_DEFAULT')
# EMAIL_USE_TLS = env('EMAIL_USE_TLS')
# EMAIL_HOST = env('EMAIL_HOST')
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# EMAIL_PORT = env('EMAIL_PORT')

# enable/disable order email notification
ORDER_EMAIL_NOTIFICATION = False

# # enable/disable order sms notification
ORDER_SMS_NOTIFICATION = False

# # AWS keys
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
# S3DIRECT_REGION = env('S3DIRECT_REGION')
# SNS_REGION = env('SNS_REGION')


# CELERY SETTINGS
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_TASK_RESULT_EXPIRES = 7 * 86400
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
BROKER_BACKEND = "redis"
BROKER_CONNECTION_TIMEOUT = 5.0
CELERY_IMPORTS = ('hul.tasks', 'misreporting.tasks')
CELERY_ENABLED = True
CELERY_TIMEZONE = TIME_ZONE
# djcelery.setup_loader()
LOGIN_URL = 'admin:login'


PIDILITE = {
    "FTP_ORDER_FILE": True,
    "TMP": join(TMP_ROOT, "pidilite"),
    "FTP": {
        # "HOST": env('PIDILITE_FTP_HOST'),
        # "USER": env('PIDILITE_FTP_USER'),
        # "PASSWORD": env('PIDILITE_FTP_PASSWORD'),
        # "PORT": env('PIDILITE_FTP_PORT'),
        "INBOUND": "Inbound",
        "OUTBOUND": "Outbound",
        "ARCHIVE": "Archive",
        "MATRD": "MATRD",
        "GSTNO": "GSTNO",
        "SFTP": True,
    },
}


PEPSICO = {
    "TMP": join(TMP_ROOT, "pepsico"),
    # "HOST": env('PEPSICO_FTP_HOST'),
    # "USER": env('PEPSICO_FTP_USER'),
    # "PKEY_PATH": env('PEPSICO_FTP_PKEY_PATH'),
    # "PKEY_PASSWORD": env('PEPSICO_FTP_PKEY_PASSWORD'),
    "INBOUND": "/IB/",
    "OUTBOUND": "/OB/",
    "ARCHIVE": "Archive",
}
