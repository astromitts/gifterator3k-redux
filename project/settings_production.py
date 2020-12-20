import os
from project.settings import *  # noqa
import dj_database_url

DATABASES['default'] = dj_database_url.config(conn_max_age=600)
DATABASES['default'] = dj_database_url.config(default=os.environ['DATABASE_URL'])

DEBUG = True

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE_DEBUG = False

HOST = 'https://gifterator3k.herokuapp.com'

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
DISPLAY_AUTH_SUCCESS_MESSAGES = False

# email settings
LOG_EMAILS = True
SEND_EMAILS = True
EMAILS_FROM = 'admin@gifterator3k.com'
EMAIL_REPLY_TO = 'admin@gifterator3k.com'
PREVIEW_EMAILS_IN_APP = False


HOST = 'http://127.0.0.1:8000'

ALLOWED_HOSTS = ['gifterator3k.herokuapp.com', 'herokuapp.com', ]
