import environ

from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

test_database_url = env.str(
    "DATABASE_URL",
    default="postgres://postgres:postgres@localhost:5432/__PROJECT_SLUG___test",
)
DATABASES = {
    "default": environ.Env.db_url_config(test_database_url),
}
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = False

# Speed up password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
