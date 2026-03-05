import os


def _float_env(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


def setup_sentry() -> None:
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
    except ImportError as exc:
        raise ImportError(
            "Sentry packages not installed. Ensure sentry-sdk is available in dependencies."
        ) from exc

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=_float_env("SENTRY_TRACES_SAMPLE_RATE", 0.0),
        profiles_sample_rate=_float_env("SENTRY_PROFILES_SAMPLE_RATE", 0.0),
        environment=os.environ.get("APP_ENV", "local"),
        release=os.environ.get("RELEASE_VERSION"),
        send_default_pii=False,
    )
