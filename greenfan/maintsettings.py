import os
import os.path
import random
import string

DEBUG = True

db = os.path.join(os.getcwd(), 'testdb.sqlite')

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': db,
  },
}

ROOT_URLCONF = 'greenfan.urls'
SITE_ID = 1
SECRET_KEY = ''.join([random.choice(string.ascii_letters) for x in range(40)])

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'greenfan',
    'south'
)

TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)
TIMEZONE = 'UTC'
