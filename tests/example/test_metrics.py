from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient


class TestMetricsEndpoint:
    @override_settings(METRICS_ENABLED=False)
    def test_returns_404_when_disabled(self, api_client: APIClient) -> None:
        response = api_client.get("/metrics")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @override_settings(METRICS_ENABLED=True, METRICS_ALLOWED_CIDRS=["10.0.0.0/8"])
    def test_rejects_non_internal_ip_without_token(self, api_client: APIClient) -> None:
        response = api_client.get("/metrics", REMOTE_ADDR="198.51.100.10")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(METRICS_ENABLED=True, METRICS_ALLOWED_CIDRS=["127.0.0.1/32"])
    def test_allows_internal_ip(self, api_client: APIClient) -> None:
        response = api_client.get("/metrics", REMOTE_ADDR="127.0.0.1")
        assert response.status_code == status.HTTP_200_OK
        assert "django_api_requests_total" in response.content.decode()

    @override_settings(
        METRICS_ENABLED=True,
        METRICS_ALLOWED_CIDRS=["10.0.0.0/8"],
        METRICS_TOKEN="shared-metrics-token",
    )
    def test_allows_valid_metrics_token(self, api_client: APIClient) -> None:
        response = api_client.get(
            "/metrics",
            REMOTE_ADDR="198.51.100.10",
            HTTP_X_METRICS_TOKEN="shared-metrics-token",
        )
        assert response.status_code == status.HTTP_200_OK
