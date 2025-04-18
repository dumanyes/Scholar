import os
from email.policy import default
from pathlib import Path

# To keep secret keys in environment variables
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.getenv('SECRET_KEY'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# ALLOWED_HOSTS = [
#     "*"
#     # etc.
# ]

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'scholarhub.kz', 'scholar-d6c0.onrender.com', 'scholarhub.up.railway.app', 'scholarhub-trkt.onrender.com']
# 'scholar-d6c0.onrender.com'


# Application definition
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users.apps.UserConfig',
    'social_django',
    'widget_tweaks',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'crispy_forms',
    'cities_light',
    'dal',
    'dal_select2',
    'channels',
    'grappelli',



    'projects',
    'ai_assistant',
    'dashboard',
    'sduNews',

]

ASGI_APPLICATION = "user_management.asgi.application"

CHANNEL_LAYERS = {
    "default": {
         "BACKEND": "channels_redis.core.RedisChannelLayer",
         "CONFIG": {
             "hosts": [ os.environ.get("REDIS_URL", "redis://default:rneGUVjlsvyflzJlrAKkJMrLbgiobrWr@switchback.proxy.rlwy.net:55870") ],
         },
    },
}


CITIES_LIGHT_TRANSLATION_LANGUAGES = ['en', 'ru']  # Языки для переводов
CITIES_LIGHT_INCLUDE_COUNTRIES = None  # All countries should be included by default
  # Пустой список означает все страны
CITIES_LIGHT_INCLUDE_CITY_TYPES = ['PPL', 'PPLA', 'PPLA2', 'PPLC']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'users.middleware.UpdateLastOnlineMiddleware',
]

ROOT_URLCONF = 'user_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'user_management.wsgi.application'

# Database

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
# DATABASE_URL = "postgresql://postgres:hnzfXICblatumDEsKpTKIYSgunxotHzn@interchange.proxy.rlwy.net:39796/railway"
# DATABASES = {
#     "default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
# }



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'scholarhub',
        'USER': 'scholaruser',
        'PASSWORD': 'strongpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# DATABASES = {
#     'default': dj_database_url.parse(
#         "postgresql://db_scholar_user:TMHTE1QV2twYKYsQPN5TtqBaLh8FLwfG@dpg-cvhljg7noe9s739jakk0-a.oregon-postgres.render.com/db_scholar",
#         conn_max_age=600,
#         ssl_require=True  # Ensures secure connection to Render-hosted Postgres
#     )
# }


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
# DATABASES['default'] = dj_database_url.parse("postgresql://scholar_t_db_01_zzjs_user:HSBY7RS1HV4CmPHVe6f52NHmcCD4OUuL@dpg-cutif3l2ng1s73datefg-a.oregon-postgres.render.com/scholar_t_db_01_zzjs")

#new db
# postgresql://scholar_t_db_01_zzjs_user:HSBY7RS1HV4CmPHVe6f52NHmcCD4OUuL@dpg-cutif3l2ng1s73datefg-a.oregon-postgres.render.com/scholar_t_db_01_zzjs

#postgresql://scholar_t_db_01_user:gLhki25VqEsUl4icyP1E25xsneJTxqS8@dpg-cus2gg23esus73fi6ns0-a.oregon-postgres.render.com/scholar_t_db_01

# Password validation
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

# Authentication Backends
AUTHENTICATION_BACKENDS = (
    'social_core.backends.github.GithubOAuth2',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.orcid.ORCIDOAuth2',

    'django.contrib.auth.backends.ModelBackend',  # Default Django authentication
)

# Social Auth Configuration
SOCIAL_AUTH_GITHUB_KEY = str(os.getenv('GITHUB_KEY'))
SOCIAL_AUTH_GITHUB_SECRET = str(os.getenv('GITHUB_SECRET'))

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "68116905972-t2olk8h12rlk254ci2ftl6ekqhtm1k11.apps.googleusercontent.com"
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "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"
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://localhost:8000/oauth/complete/google-oauth2/'


SOCIAL_AUTH_ORCID_REDIRECT_URI = 'http://127.0.0.1:8000/oauth/complete/orcid/'
SOCIAL_AUTH_ORCID_KEY = 'APP-T3JVRI0BX1B3LKAL'  # Replace with your actual ORCID client ID
SOCIAL_AUTH_ORCID_SECRET = 'f5fdc6ba-f8eb-406d-a0af-883cc48f505e'  # Replace with your actual ORCID client secret


# Redirect URLs after login and logout
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'



# Email configurations (if you use email for registration/reset)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'dopoinaiyq@gmail.com'
EMAIL_HOST_PASSWORD = 'uyvaselsniqveqlo'
DEFAULT_FROM_EMAIL = 'dopoinaiyq@gmail.com'
# Session settings
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Site ID for allauth
SITE_ID = 1

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
X_FRAME_OPTIONS = 'SAMEORIGIN'

CRISPY_TEMPLATE_PACK = 'bootstrap5'  # Or 'bootstrap4', depending on your version of Bootstrap

TIME_ZONE = "Asia/Yekaterinburg"

