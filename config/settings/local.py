import environ

from .base import *  # noqa: F401, F403
from .base import APP_ENV, BASE_DIR, LOG_LEVEL, SERVICE_NAME

environ.Env.read_env(BASE_DIR / ".env", overwrite=True)

DEBUG = True

# Re-configure with console renderer for local development
from config.logging import configure_logging  # noqa: E402

configure_logging(
    log_level=LOG_LEVEL,
    json_logs=False,
    service_name=SERVICE_NAME,
    environment=APP_ENV,
)

INSTALLED_APPS = [  # noqa: F405
    *INSTALLED_APPS,  # noqa: F405
    "django.contrib.admindocs",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
