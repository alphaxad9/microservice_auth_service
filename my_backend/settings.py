
from datetime import timedelta
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

RABBITMQ = {
    "HOST": os.getenv("RABBITMQ_HOST", "localhost"),
    "PORT": int(os.getenv("RABBITMQ_PORT", 5672)),
    "USER": os.getenv("RABBITMQ_USER", "guest"),
    "PASS": os.getenv("RABBITMQ_PASS", "guest"),
    "VHOST": os.getenv("RABBITMQ_VHOST", "/"),
    "QUEUE": os.getenv("RABBITMQ_QUEUE", "default.events"),
}
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'src.infrastructure.apps.users',
    'src.infrastructure.apps.profiles',
    'src.infrastructure.apps.outbox',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    'rest_framework',
    'rest_framework_simplejwt'


]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_backend.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'my_backend.wsgi.application'

ASGI_APPLICATION = 'my_backend.asgi.application'
DATABASES = {
    "default": {
        "ENGINE": os.getenv("POSTGRES_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("POSTGRES_DB", "authdb"),
        "USER": os.getenv("POSTGRES_USER", "ishimwe"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

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


LANGUAGE_CODE = os.getenv('DJANGO_LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'UTC')


USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # OLD
STATIC_ROOT = '/app/static'  # NEW - matches Kubernetes mount

# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # OLD  
MEDIA_ROOT = '/app/media'  # NEW - matches Kubernetes mount
MEDIA_URL = '/media/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'src.infrastructure.apps.users.authenticate.JWTCookieAuthentication', 
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
'rest_framework.permissions.IsAuthenticated',    ]
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "formatters": {
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "loggers": {
        # Root logger
        "": {
            "handlers": ["console"],
            "level": os.getenv('LOG_LEVEL', 'INFO'),
        },
    },
}

AUTH_USER_MODEL = 'users.ORMUser'


CHANNEL_LAYER_HOSTS = os.getenv('CHANNEL_LAYER_HOSTS', '127.0.0.1:6379').split(',')

# In settings.py, add after your CHANNEL_LAYERS config:

# Get Redis password from environment
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis.infrastructure.svc.cluster.local')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')

# Build Redis URL with password
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],  # ← String URL, NOT tuple!
            "capacity": int(os.getenv('CHANNEL_LAYER_CAPACITY', 1000)),
            "expiry": int(os.getenv('CHANNEL_LAYER_EXPIRY', 10)),
        },
    },
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "RS256",
    "SIGNING_KEY": os.getenv("SIGNING_KEY"),
    "VERIFYING_KEY": os.getenv("VERIFYING_KEY"),
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",

    'AUTH_COOKIE': 'access',
    'AUTH_COOKIE_REFRESH': 'refresh',
    'AUTH_COOKIE_SECURE': False,  # False for dev
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'None',
}
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
]
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'True').lower() == 'true'
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',  
]

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY",)