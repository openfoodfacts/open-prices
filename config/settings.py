import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Directory where user-uploaded images are stored
IMAGES_DIR = BASE_DIR / "img"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "set-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG") == "True"
TESTING = "test" in sys.argv

ALLOWED_HOSTS = [x.strip() for x in os.getenv("ALLOWED_HOSTS", "").split(",")]


# App config
# ------------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "corsheaders",  # django-cors-headers
    "rest_framework",  # djangorestframework
    "django_filters",  # django-filter
    "drf_spectacular",  # drf-spectacular
    "django_q",  # django-q2
    # "debug_toolbar",  # django-debug-toolbar (see below)
    "django_extensions",  # django-extensions
]

LOCAL_APPS = [
    "open_prices.common",
    "open_prices.products",
    "open_prices.locations",
    "open_prices.proofs",
    "open_prices.prices",
    "open_prices.users",
    "open_prices.api",
    "open_prices.www",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

APPEND_SLASH = False

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "open_prices/templates")],
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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# ------------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "USER": os.getenv("POSTGRES_USER"),
        "NAME": os.getenv("POSTGRES_DB"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
        "CONN_MAX_AGE": 60,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
# ------------------------------------------------------------------------------

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
# ------------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
# ------------------------------------------------------------------------------

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
# ------------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Security
# ------------------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# Django REST Framework (DRF) & django-filters & drf-spectacular
# https://www.django-rest-framework.org/
# https://django-filter.readthedocs.io/
# https://drf-spectacular.readthedocs.io/
# ------------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "open_prices.common.middleware.custom_exception_handler",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "ORDERING_PARAM": "order_by",
    "DEFAULT_PAGINATION_CLASS": "open_prices.api.pagination.CustomPagination",
    "PAGE_SIZE": 100,
    "COERCE_DECIMAL_TO_STRING": False,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Open Food Facts open-prices REST API",
    "DESCRIPTION": "Open Prices API allows you to add product prices",
    "CONTACT": {
        "name": "The Open Food Facts team",
        "url": "https://world.openfoodfacts.org",
        "email": "contact@openfoodfacts.org",
    },
    "LICENSE": {
        "name": " AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
    },
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
    "ENUM_NAME_OVERRIDES": {
        "LocationOsmTypeEnum": "open_prices.locations.constants.OSM_TYPE_CHOICES"
    },
}


# Django Q2
# https://django-q2.readthedocs.io/
# ------------------------------------------------------------------------------

Q_CLUSTER = {
    "name": "DjangORM",
    "workers": 2,
    "timeout": 2 * 60 * 60,  # 2h
    "retry": 2 * 60 * 60 + 1,
    "max_attempts": 1,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
    "sync": True if DEBUG else False,
}


# Sentry
# https://docs.sentry.io/platforms/python/integrations/django/
# ------------------------------------------------------------------------------

if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        environment=os.getenv("ENVIRONMENT"),
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for tracing.  # noqa
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.  # noqa
        # We recommend adjusting this value in production.
        # profiles_sample_rate=1.0,
    )


# Django Debug Toolbar
# https://django-debug-toolbar.readthedocs.io/
# ------------------------------------------------------------------------------

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]


# Django-extensions
# https://django-extensions.readthedocs.io/
# ------------------------------------------------------------------------------

SHELL_PLUS = "ipython"
SHELL_PLUS_POST_IMPORTS = [
    "import openfoodfacts",
    "from open_prices.common import openfoodfacts as common_openfoodfacts",
    "from open_prices.common import openstreetmap as common_openstreetmap",
    "from open_prices.common import tasks as common_tasks",
]


# Authentication
# ------------------------------------------------------------------------------

OAUTH2_SERVER_URL = os.getenv("OAUTH2_SERVER_URL")
SESSION_COOKIE_NAME = "opsession"
OFF_USER_AGENT = "open-prices/0.1.0"
