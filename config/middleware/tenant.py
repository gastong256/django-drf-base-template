import re
from collections.abc import Callable

import structlog
from django.http import HttpRequest, HttpResponse

from config.context import tenant_id_var

TENANT_HEADER = "HTTP_X_TENANT_ID"
DEFAULT_TENANT = "public"
TENANT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")

logger = structlog.get_logger(__name__)


def _normalize_tenant_id(raw_value: str | None) -> str:
    if raw_value is None:
        return DEFAULT_TENANT

    candidate = raw_value.strip().lower()
    if not candidate:
        return DEFAULT_TENANT

    if not TENANT_PATTERN.fullmatch(candidate):
        logger.warning("invalid_tenant_header", provided_tenant_id=raw_value)
        return DEFAULT_TENANT

    return candidate


class TenantMiddleware:
    """
    Resolves tenant from X-Tenant-ID request header.
    Falls back to "public" if the header is absent.
    The resolved tenant_id is stored in a ContextVar so it is available
    throughout the request lifecycle (logs, services, queries).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        tenant_id = _normalize_tenant_id(request.META.get(TENANT_HEADER))
        tenant_id_var.set(tenant_id)
        request.tenant_id = tenant_id  # type: ignore[attr-defined]
        return self.get_response(request)
