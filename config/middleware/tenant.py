import re
from collections.abc import Callable

import structlog
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.tenants.models import Tenant
from config.context import tenant_id_var, tenant_pk_var

TENANT_HEADER = "HTTP_X_TENANT_ID"
DEFAULT_TENANT = "public"
TENANT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
SKIP_TENANT_VALIDATION_PREFIXES = (
    "/healthz",
    "/readyz",
    "/metrics",
    "/api/openapi.json",
    "/api/docs",
    "/api/redoc",
    "/admin/",
    "/static/",
)

logger = structlog.get_logger(__name__)


def _normalize_tenant_id(raw_value: str | None) -> str | None:
    if raw_value is None:
        return DEFAULT_TENANT

    candidate = raw_value.strip().lower()
    if not candidate:
        return DEFAULT_TENANT

    if not TENANT_PATTERN.fullmatch(candidate):
        return None

    return candidate


def _should_skip_tenant_validation(path: str) -> bool:
    return path in {"/healthz", "/readyz"} or any(
        path.startswith(prefix) for prefix in SKIP_TENANT_VALIDATION_PREFIXES
    )


class TenantMiddleware:
    """
    Resolves and validates tenant from X-Tenant-ID request header.
    Falls back to "public" if the header is absent.
    Invalid/inactive tenants are rejected with HTTP 400.
    The resolved tenant id and pk are stored in ContextVars so they are available
    throughout the request lifecycle (logs, services, queries).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if _should_skip_tenant_validation(request.path):
            tenant_id_var.set(DEFAULT_TENANT)
            tenant_pk_var.set(None)
            request.tenant_id = DEFAULT_TENANT  # type: ignore[attr-defined]
            return self.get_response(request)

        tenant_id = _normalize_tenant_id(request.META.get(TENANT_HEADER))
        if tenant_id is None:
            logger.warning("invalid_tenant_header", provided_tenant_id=request.META.get(TENANT_HEADER))
            return JsonResponse(
                {
                    "error": {
                        "code": "invalid_tenant",
                        "message": "Tenant is invalid or inactive.",
                        "detail": None,
                    }
                },
                status=400,
            )

        try:
            tenant = Tenant.objects.only("id", "slug").get(slug=tenant_id, is_active=True)
        except Tenant.DoesNotExist:
            logger.warning("invalid_tenant_header", provided_tenant_id=tenant_id)
            return JsonResponse(
                {
                    "error": {
                        "code": "invalid_tenant",
                        "message": "Tenant is invalid or inactive.",
                        "detail": None,
                    }
                },
                status=400,
            )
        except DatabaseError:
            logger.exception("tenant_resolution_db_error")
            return JsonResponse(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "Tenant resolution unavailable.",
                        "detail": None,
                    }
                },
                status=503,
            )

        tenant_id_var.set(tenant.slug)
        tenant_pk_var.set(tenant.id)
        request.tenant_id = tenant.slug  # type: ignore[attr-defined]
        request.tenant_pk = tenant.id  # type: ignore[attr-defined]
        return self.get_response(request)
