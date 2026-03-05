import logging
import re
import sys
from typing import Any

import structlog

from config.context import request_id_var, tenant_id_var

_service_name = "__SERVICE_NAME__"
_environment = "local"
_SENSITIVE_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "access",
    "refresh",
)
_BEARER_PATTERN = re.compile(r"(Bearer\s+)[^\s,;]+", re.IGNORECASE)


def _redact_value(value: Any, key_hint: str = "") -> Any:
    lowered_key = key_hint.lower()
    if any(marker in lowered_key for marker in _SENSITIVE_KEY_MARKERS):
        return "[REDACTED]"

    if isinstance(value, dict):
        return {k: _redact_value(v, key_hint=k) for k, v in value.items()}

    if isinstance(value, list):
        return [_redact_value(item, key_hint=key_hint) for item in value]

    if isinstance(value, tuple):
        return tuple(_redact_value(item, key_hint=key_hint) for item in value)

    if isinstance(value, str):
        return _BEARER_PATTERN.sub(r"\1[REDACTED]", value)

    return value


def _redact_sensitive_fields(
    logger: Any,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    for key in list(event_dict.keys()):
        event_dict[key] = _redact_value(event_dict[key], key_hint=key)
    return event_dict


def _add_request_context(
    logger: Any,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    event_dict["request_id"] = request_id_var.get()
    event_dict["tenant_id"] = tenant_id_var.get()
    return event_dict


def _add_trace_context(
    logger: Any,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    try:
        from opentelemetry import trace
    except ImportError:
        return event_dict

    span = trace.get_current_span()
    if span is None:
        return event_dict

    span_context = span.get_span_context()
    if not span_context or not span_context.is_valid:
        return event_dict

    event_dict["trace_id"] = f"{span_context.trace_id:032x}"
    event_dict["span_id"] = f"{span_context.span_id:016x}"
    return event_dict


def _add_service_context(
    logger: Any,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    event_dict["service"] = _service_name
    event_dict["environment"] = _environment
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    *,
    service_name: str = "__SERVICE_NAME__",
    environment: str = "local",
) -> None:
    global _service_name, _environment
    _service_name = service_name
    _environment = environment

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _add_request_context,
        _add_trace_context,
        _add_service_context,
        _redact_sensitive_fields,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "django.request"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
