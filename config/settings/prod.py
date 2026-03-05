from .base import *  # noqa: F401, F403
from .base import SECRET_KEY, env

_UNSAFE_DEFAULTS = {
    "unsafe-default-do-not-use-in-production",
    "__DJANGO_SECRET_KEY__",
    "",
}
if not SECRET_KEY or SECRET_KEY in _UNSAFE_DEFAULTS:
    raise RuntimeError(
        "DJANGO_SECRET_KEY is not set or still contains an unsafe placeholder. "
        "Set a real secret key via the DJANGO_SECRET_KEY environment variable."
    )

DEBUG = False

SECURE_PROXY_SSL_HEADER = (
    env("SECURE_PROXY_SSL_HEADER_NAME", default="HTTP_X_FORWARDED_PROTO"),
    env("SECURE_PROXY_SSL_HEADER_VALUE", default="https"),
)
USE_X_FORWARDED_HOST = env.bool("USE_X_FORWARDED_HOST", default=True)

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = env(
    "SECURE_REFERRER_POLICY",
    default="strict-origin-when-cross-origin",
)
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = env("SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_HTTPONLY = env.bool("CSRF_COOKIE_HTTPONLY", default=True)
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = env("CSRF_COOKIE_SAMESITE", default="Lax")
