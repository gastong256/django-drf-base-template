from datetime import timedelta
from pathlib import Path

import environ

from config.logging import configure_logging
from config.otel import setup_otel
from config.sentry import setup_sentry

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    RATE_LIMIT_ANON=(str, "60/minute"),
    RATE_LIMIT_USER=(str, "300/minute"),
    JWT_ACCESS_MINUTES=(int, 15),
    JWT_REFRESH_DAYS=(int, 7),
    SERVICE_NAME=(str, "__SERVICE_NAME__"),
    APP_ENV=(str, "local"),
    METRICS_ENABLED=(bool, False),
    METRICS_ALLOWED_CIDRS=(list, ["127.0.0.1/32", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]),
    METRICS_TOKEN=(str, ""),
    LOG_LEVEL=(str, "INFO"),
    OTEL_ENABLED=(bool, False),
    REDIS_URL=(str, ""),
    CELERY_BROKER_URL=(str, ""),
    CELERY_RESULT_BACKEND=(str, ""),
    READINESS_CHECK_REDIS=(bool, False),
    READINESS_REDIS_TIMEOUT_SECONDS=(int, 2),
    DB_CONN_MAX_AGE=(int, 60),
    DB_CONN_HEALTH_CHECKS=(bool, True),
    DB_CONNECT_TIMEOUT_SECONDS=(int, 5),
    DB_STATEMENT_TIMEOUT_MS=(int, 0),
    CELERY_CONCURRENCY=(int, 2),
    CELERY_MAX_TASKS_PER_CHILD=(int, 1000),
    CELERY_TASK_SOFT_TIME_LIMIT_SECONDS=(int, 300),
    CELERY_TASK_TIME_LIMIT_SECONDS=(int, 360),
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
)

environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="unsafe-default-do-not-use-in-production")
DEBUG = env.bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS")
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")
REDIS_URL = env.str("REDIS_URL")
SERVICE_NAME = env.str("SERVICE_NAME")
APP_ENV = env.str("APP_ENV")
METRICS_ENABLED = env.bool("METRICS_ENABLED")
METRICS_ALLOWED_CIDRS = env.list("METRICS_ALLOWED_CIDRS")
METRICS_TOKEN = env.str("METRICS_TOKEN")

CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default=REDIS_URL or "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
READINESS_CHECK_REDIS = env.bool("READINESS_CHECK_REDIS")
READINESS_REDIS_TIMEOUT_SECONDS = env.int("READINESS_REDIS_TIMEOUT_SECONDS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "apps.accounts",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "apps.tenants",
    "apps.example",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "config.middleware.request_id.RequestIDMiddleware",
    "config.middleware.tenant.TenantMiddleware",
    "config.metrics.MetricsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE")
DATABASES["default"]["CONN_HEALTH_CHECKS"] = env.bool("DB_CONN_HEALTH_CHECKS")

if "postgresql" in DATABASES["default"]["ENGINE"]:
    db_options = DATABASES["default"].setdefault("OPTIONS", {})
    db_connect_timeout = env.int("DB_CONNECT_TIMEOUT_SECONDS")
    if db_connect_timeout > 0:
        db_options.setdefault("connect_timeout", db_connect_timeout)

    db_statement_timeout_ms = env.int("DB_STATEMENT_TIMEOUT_MS")
    if db_statement_timeout_ms > 0:
        statement_timeout_option = f"-c statement_timeout={db_statement_timeout_ms}"
        existing_options = db_options.get("options", "")
        if statement_timeout_option not in existing_options:
            db_options["options"] = f"{existing_options} {statement_timeout_option}".strip()

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env.str("RATE_LIMIT_ANON"),
        "user": env.str("RATE_LIMIT_USER"),
    },
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS")),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": False,
}

# Celery defaults are tuned for reliability in API backends.
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_CONCURRENCY = env.int("CELERY_CONCURRENCY")
CELERY_WORKER_MAX_TASKS_PER_CHILD = env.int("CELERY_MAX_TASKS_PER_CHILD")
CELERY_TASK_SOFT_TIME_LIMIT = env.int("CELERY_TASK_SOFT_TIME_LIMIT_SECONDS")
CELERY_TASK_TIME_LIMIT = env.int("CELERY_TASK_TIME_LIMIT_SECONDS")
CELERY_TASK_TRACK_STARTED = True

SPECTACULAR_SETTINGS = {
    "TITLE": "__PROJECT_NAME__",
    "DESCRIPTION": "__DESCRIPTION__",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CONTACT": {"name": "__OWNER__"},
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
}

LOG_LEVEL = env.str("LOG_LEVEL")
JSON_LOGS = env.bool("JSON_LOGS", default=True)
configure_logging(
    log_level=LOG_LEVEL,
    json_logs=JSON_LOGS,
    service_name=SERVICE_NAME,
    environment=APP_ENV,
)

setup_sentry()
setup_otel()
