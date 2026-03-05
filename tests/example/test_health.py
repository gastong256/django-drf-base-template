from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient


class TestLivenessEndpoint:
    def test_returns_ok(self, api_client: APIClient) -> None:
        response = api_client.get("/healthz")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok"}

    def test_ignores_invalid_tenant_header(self, api_client: APIClient) -> None:
        response = api_client.get("/healthz", HTTP_X_TENANT_ID="invalid tenant id")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestReadinessEndpoint:
    def test_returns_ok_when_db_available(self, api_client: APIClient) -> None:
        response = api_client.get("/readyz")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok"}

    def test_returns_503_when_redis_check_enabled_without_url(
        self, api_client: APIClient, settings
    ) -> None:
        settings.READINESS_CHECK_REDIS = True
        settings.REDIS_URL = ""

        response = api_client.get("/readyz")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()["detail"] == "Redis unavailable."

    @patch("config.urls.redis.Redis.from_url")
    def test_returns_ok_when_redis_is_available(
        self, mock_from_url: MagicMock, api_client: APIClient, settings
    ) -> None:
        settings.READINESS_CHECK_REDIS = True
        settings.REDIS_URL = "redis://localhost:6379/0"
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client

        response = api_client.get("/readyz")
        assert response.status_code == status.HTTP_200_OK

    @patch("config.urls.redis.Redis.from_url")
    def test_returns_503_when_redis_is_unavailable(
        self, mock_from_url: MagicMock, api_client: APIClient, settings
    ) -> None:
        settings.READINESS_CHECK_REDIS = True
        settings.REDIS_URL = "redis://localhost:6379/0"
        mock_client = MagicMock()
        mock_client.ping.side_effect = RuntimeError("redis down")
        mock_from_url.return_value = mock_client

        response = api_client.get("/readyz")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()["detail"] == "Redis unavailable."
