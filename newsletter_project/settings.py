import os 
from pathlib import Path
from dotenv import load_dotenv
import os
#from django.contrib.sites.models import Site
from decouple import config
import pymysql
import os
 
pymysql.install_as_MySQLdb()
 
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'environment.env')

# Charger les variables d'environnement
load_dotenv(dotenv_path)

# Charger les clés Stripe à partir des variables d'environnement
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
  
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY        = os.getenv('SECRET_KEY')
DEBUG             =  True

ALLOWED_HOSTS =  ['127.0.0.1', 'localhost']     #os.getenv('ALLOWED_HOSTS').split(',')
 
INSTALLED_APPS = [
  #  'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.subscriptions',
    'apps.newsletters',
  #  'django_cron',
    'apps.custom_admin',
    'django.contrib.admin',  # Django's admin app
    'django.contrib.sites',
    #'rest_framework',  # if you plan to use Django Rest Framework
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'crispy_forms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
 
STATIC_URL = '/static/'
 
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
 
ROOT_URLCONF = "newsletter_project.urls"
  
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
            ],
        },
    },
]

WSGI_APPLICATION = "newsletter_project.wsgi.application"

# Stocker les sessions dans la base de données
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  
 
SESSION_COOKIE_AGE = 1209600  # 2 semaines
 
SESSION_COOKIE_SECURE = False   
SESSION_EXPIRE_AT_BROWSER_CLOSE = False   
   
# print("ENGINE:", os.getenv('ENGINE'))
# print("DATABASE NAME:", os.getenv('NAME_DB'))
# print("USER:", os.getenv('USER_DB'))
# print("PASSWORD:", os.getenv('PASSWORD_DB'))
# print("HOST:", os.getenv('HOST_DB'))
# print("PORT:", os.getenv('PORT'))
# print("PORALLOWED_HOSTST:", os.getenv('ALLOWED_HOSTS'))
  
  
DATABASES = {
    'default': {
        'ENGINE': os.getenv('ENGINE') ,
        'NAME': os.getenv('NAME_DB'),   
        'USER':  os.getenv('USER_DB')   ,
        'PASSWORD': os.getenv('PASSWORD_DB'),   
        'HOST': os.getenv('HOST_DB'),   
        'PORT': os.getenv('PORT'),
        'OPTIONS': {
            'ssl': {'ssl-mode': os.getenv('SSL_MODE' )},   
        }
    }
}
 
CRON_CLASSES = [
    'apps.subscriptions.cron.ResetSubscriptionCronJob',
]
 
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
 
LANGUAGE_CODE = "en-us" 
TIME_ZONE = "UTC" 
USE_I18N = True 
USE_TZ = True
  
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
] 
  
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID =1
 
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
  
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
   
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_SECRET_KEY'),
        }
    }
}
 

# Configuration pour django-crispy-forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'
 
AUTH_USER_MODEL = 'accounts.CustomUser'
  
# Base directory path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
# Static files directory
SOCIALACCOUNT_LOGIN_ON_GET = True

ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

ACCOUNT_EMAIL_VERIFICATION = "none"   
SOCIALACCOUNT_AUTO_SIGNUP = True     
     
EMAIL_BACKEND       = os.getenv('EMAIL_BACKEND')
EMAIL_HOST          = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT          = os.getenv('EMAIL_PORT')
SENDER_EMAIL        = os.getenv('SENDER_EMAIL')
DEFAULT_FROM_EMAIL =   SENDER_EMAIL                
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
PASSWORD_RESET_TIMEOUT = 259200  # 3 jourson fait :