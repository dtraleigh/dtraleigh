import os
from pathlib import Path
import environ

env = environ.Env(DEBUG=(bool, False))
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET")

if env("DJANGO_DEBUG") == "1":
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "develop.dtraleigh.com", "dtraleigh.cophead567.opalstacked.com"]

INTERNAL_IPS = [
    "127.0.0.1",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django_extensions",
    "develop",
    "simple_history",
    "leaflet",
    "buildings",
    "newBernTOD",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "myproject.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DEFAULT_DB_NAME"),
        "USER": env("DEFAULT_DB_USER"),
        "PASSWORD": env("DEFAULT_DB_PASS"),
        "HOST": env("DEFAULT_DB_HOST"),
        "PORT": env("DEFAULT_DB_PORT"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

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
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "static/"
if env("DJANGO_DEBUG") == "1":
    STATIC_ROOT = os.path.join(BASE_DIR, "static/")
else:
    STATIC_ROOT = "/home/cophead567/apps/dtraleigh_static/"

# STATICFILES_DIRS = (
#     "/home/cophead567/apps/develop/myproject/static/",
# )

# MEDIA_URL = "https://develop.dtraleigh.com/static/uploads/"
# MEDIA_ROOT = "/home/cophead567/apps/develop_static/uploads"

ADMINS = (
    ("Leo", "leo@dtraleigh.com"),
)

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = False
FILE_UPLOAD_PERMISSIONS = 0o664

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_TIMEOUT = 10

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',"
                      "'%m-%d %H:%M:%S'"
        },
        "simple": {
            "format": "%(levelname)s %(message)s"
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "debug.txt",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

GDAL_LIBRARY_PATH = env("GDAL_LIBRARY_PATH")
X_FRAME_OPTIONS = "SAMEORIGIN"

LEAFLET_CONFIG = {
    "DEFAULT_CENTER": (35.7785733, -78.6395438),
    "DEFAULT_ZOOM": 18,
    "MAX_ZOOM": 20,
    "MIN_ZOOM": 3,
    "SCALE": "both"
}
