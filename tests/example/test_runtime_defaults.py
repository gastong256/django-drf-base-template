from django.conf import settings


def test_celery_runtime_limits_are_configured() -> None:
    assert settings.CELERY_TASK_SOFT_TIME_LIMIT > 0
    assert settings.CELERY_TASK_TIME_LIMIT >= settings.CELERY_TASK_SOFT_TIME_LIMIT
    assert settings.CELERY_WORKER_MAX_TASKS_PER_CHILD > 0


def test_db_connection_health_checks_setting_exists() -> None:
    assert "CONN_HEALTH_CHECKS" in settings.DATABASES["default"]
