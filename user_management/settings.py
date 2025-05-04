import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1', 'localhost',
    'scholarhub.kz',
    'scholar-d6c0.onrender.com',
    'scholarhub.up.railway.app',
    'scholarhub-trkt.onrender.com'
]

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
    'projects',
    'ai_assistant',
    'dashboard',
    'sduNews',

    'widget_tweaks',
    'social_django',
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
]

SITE_ID = 1

ASGI_APPLICATION = "user_management.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}

LANGUAGE_CODE = 'en-us'
LANGUAGES = [
    ('en', 'English'),
    ('ru', 'Russian'),
    ('kk', 'Kazakh'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

CITIES_LIGHT_TRANSLATION_LANGUAGES = ['en', 'ru']
CITIES_LIGHT_INCLUDE_COUNTRIES = None
CITIES_LIGHT_INCLUDE_CITY_TYPES = ['PPL', 'PPLA', 'PPLA2', 'PPLC']

TIME_ZONE = "Asia/Yekaterinburg"
USE_I18N = True
USE_L10N = True

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
    'django.middleware.locale.LocaleMiddleware',
    'users.middleware.ProfileLanguageMiddleware',
    'users.middleware.ForceSetPasswordMiddleware',
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

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST'),
#         'PORT': os.getenv('DB_PORT'),
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

AUTHENTICATION_BACKENDS = (
    'social_core.backends.github.GithubOAuth2',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.orcid.ORCIDOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI")

SOCIAL_AUTH_ORCID_KEY = os.getenv("SOCIAL_AUTH_ORCID_KEY")
SOCIAL_AUTH_ORCID_SECRET = os.getenv("SOCIAL_AUTH_ORCID_SECRET")
SOCIAL_AUTH_ORCID_REDIRECT_URI = os.getenv("SOCIAL_AUTH_ORCID_REDIRECT_URI")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.zoho.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASSWORD")
DEFAULT_FROM_EMAIL = f"ScholarHub <{EMAIL_HOST_USER}>"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
X_FRAME_OPTIONS = 'SAMEORIGIN'

CRISPY_TEMPLATE_PACK = 'bootstrap5'
