import re
import uuid
from collections.abc import Callable

import structlog

from django.http import HttpRequest, HttpResponse

from config.context import request_id_var

REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
RESPONSE_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

logger = structlog.get_logger(__name__)


def _normalize_request_id(raw_value: str | None) -> str:
    if raw_value is None:
        return str(uuid.uuid4())

    candidate = raw_value.strip()
    if not candidate:
        return str(uuid.uuid4())

    if not REQUEST_ID_PATTERN.fullmatch(candidate):
        logger.warning("invalid_request_id_header", provided_request_id=raw_value)
        return str(uuid.uuid4())

    return candidate


class RequestIDMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = _normalize_request_id(request.META.get(REQUEST_ID_HEADER))
        request_id_var.set(request_id)
        request.request_id = request_id  # type: ignore[attr-defined]

        response = self.get_response(request)
        response[RESPONSE_HEADER] = request_id
        return response
