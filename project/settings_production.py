import os
from project.settings import *  # noqa
import dj_database_url

DATABASES['default'] = dj_database_url.config(conn_max_age=600)
DATABASES['default'] = dj_database_url.config(default=os.environ['DATABASE_URL'])

DEBUG = True

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE_DEBUG = False

HOST = 'https://gifterator3k.herokuapp.com/'

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

ALLOWED_HOSTS = ['gifterator3k.herokuapp.com', 'herokuapp.com', ]
