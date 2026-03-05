import redis
import structlog

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

logger = structlog.get_logger(__name__)

_status_response = inline_serializer(
    name="StatusResponse",
    fields={"status": serializers.CharField()},
)


class LivenessView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="liveness",
        summary="Liveness probe",
        responses={200: _status_response},
        tags=["health"],
    )
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class ReadinessView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="readiness",
        summary="Readiness probe",
        responses={
            200: _status_response,
            503: OpenApiResponse(description="Database unavailable"),
        },
        tags=["health"],
    )
    def get(self, request: Request) -> Response:
        from django.db import connection

        try:
            connection.ensure_connection()
        except Exception:
            logger.exception("readiness_check_failed")
            return Response(
                {"status": "unavailable", "detail": "Database unavailable."},
                status=503,
            )

        if settings.READINESS_CHECK_REDIS:
            if not settings.REDIS_URL:
                logger.error("readiness_redis_not_configured")
                return Response(
                    {"status": "unavailable", "detail": "Redis unavailable."},
                    status=503,
                )

            try:
                redis_client = redis.Redis.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=settings.READINESS_REDIS_TIMEOUT_SECONDS,
                    socket_timeout=settings.READINESS_REDIS_TIMEOUT_SECONDS,
                )
                redis_client.ping()
            except Exception:
                logger.exception("readiness_redis_check_failed")
                return Response(
                    {"status": "unavailable", "detail": "Redis unavailable."},
                    status=503,
                )

        return Response({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", LivenessView.as_view(), name="liveness"),
    path("readyz", ReadinessView.as_view(), name="readiness"),
    path("api/v1/auth/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/", include("apps.accounts.api.urls")),
    # OpenAPI
    path("api/openapi.json", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Versioned API
    path("api/v1/", include("apps.example.api.urls")),
]
