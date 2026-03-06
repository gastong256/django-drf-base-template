import ipaddress
from time import perf_counter
from typing import Any, cast

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from drf_spectacular.utils import extend_schema
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Histogram,
    generate_latest,
)
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


def _get_counter(name: str, documentation: str, labelnames: tuple[str, ...]) -> Counter:
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return cast(Counter, existing)
    return Counter(name, documentation, labelnames=labelnames)


def _get_histogram(name: str, documentation: str, labelnames: tuple[str, ...]) -> Histogram:
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return cast(Histogram, existing)
    return Histogram(
        name,
        documentation,
        labelnames=labelnames,
        buckets=(0.01, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0),
    )


REQUEST_COUNT = _get_counter(
    "django_api_requests_total",
    "Total API requests processed by Django.",
    ("method", "view", "status"),
)
REQUEST_LATENCY = _get_histogram(
    "django_api_request_duration_seconds",
    "API request latency in seconds.",
    ("method", "view"),
)


def _get_view_label(request: HttpRequest) -> str:
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match and resolver_match.view_name:
        return resolver_match.view_name
    return request.path


def _track_request_metrics(request: HttpRequest, status_code: int, duration_seconds: float) -> None:
    view_label = _get_view_label(request)
    REQUEST_COUNT.labels(
        method=request.method,
        view=view_label,
        status=str(status_code),
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        view=view_label,
    ).observe(duration_seconds)


class MetricsMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not settings.METRICS_ENABLED:
            return self.get_response(request)

        started_at = perf_counter()
        try:
            response = self.get_response(request)
        except Exception:
            _track_request_metrics(
                request,
                status_code=500,
                duration_seconds=perf_counter() - started_at,
            )
            raise

        _track_request_metrics(
            request,
            status_code=response.status_code,
            duration_seconds=perf_counter() - started_at,
        )
        return response


def _parse_allowed_networks(raw_value: Any) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    if isinstance(raw_value, str):
        candidates = [part.strip() for part in raw_value.split(",") if part.strip()]
    else:
        candidates = [str(part).strip() for part in raw_value if str(part).strip()]

    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for candidate in candidates:
        try:
            networks.append(ipaddress.ip_network(candidate, strict=False))
        except ValueError:
            continue
    return networks


def _get_client_ip(request: Request) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        raw_ip = forwarded_for.split(",")[0].strip()
    else:
        raw_ip = request.META.get("REMOTE_ADDR", "").strip()

    if not raw_ip:
        return None

    try:
        return ipaddress.ip_address(raw_ip)
    except ValueError:
        return None


class InternalMetricsPermission(BasePermission):
    message = "Metrics endpoint is restricted."

    def has_permission(self, request: Request, view: APIView) -> bool:  # noqa: ARG002
        if not settings.METRICS_ENABLED:
            # Keep endpoint hidden with 404 in the view when metrics are off.
            return True

        metrics_token = settings.METRICS_TOKEN
        provided_token = request.META.get("HTTP_X_METRICS_TOKEN", "")
        if metrics_token and provided_token and metrics_token == provided_token:
            return True

        client_ip = _get_client_ip(request)
        if client_ip is None:
            return False

        allowed_networks = _parse_allowed_networks(settings.METRICS_ALLOWED_CIDRS)
        return any(client_ip in network for network in allowed_networks)


class MetricsView(APIView):
    authentication_classes: list = []
    permission_classes = [InternalMetricsPermission]

    @extend_schema(exclude=True)
    def get(self, request: Request) -> HttpResponse:  # noqa: ARG002
        if not settings.METRICS_ENABLED:
            raise Http404

        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)