import pytest
from rest_framework.test import APIClient

from apps.tenants.models import Tenant


@pytest.fixture
def api_client(db) -> APIClient:  # noqa: ARG001
    Tenant.objects.get_or_create(slug="public", defaults={"name": "Public", "is_active": True})
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, django_user_model: type) -> APIClient:
    user = django_user_model.objects.create_user(username="testuser", password="pass")
    api_client.force_authenticate(user=user)
    return api_client
