import uuid

import pytest
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.permissions import ROLE_READER
from apps.example.models import Item
from apps.tenants.models import Tenant
from config.context import tenant_id_var


@pytest.mark.django_db
class TestPingEndpoint:
    def test_returns_pong(self, api_client: APIClient) -> None:
        response = api_client.get("/api/v1/ping")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "pong"}

    def test_includes_request_id_header(self, api_client: APIClient) -> None:
        response = api_client.get("/api/v1/ping")
        assert "X-Request-ID" in response

    def test_preserves_valid_request_id_header(self, api_client: APIClient) -> None:
        response = api_client.get("/api/v1/ping", HTTP_X_REQUEST_ID="trace-123")
        assert response["X-Request-ID"] == "trace-123"

    def test_replaces_invalid_request_id_header(self, api_client: APIClient) -> None:
        invalid_request_id = "bad request id"
        response = api_client.get("/api/v1/ping", HTTP_X_REQUEST_ID=invalid_request_id)
        assert response["X-Request-ID"] != invalid_request_id
        assert response["X-Request-ID"]

    def test_normalizes_tenant_header_to_lowercase(self, api_client: APIClient) -> None:
        Tenant.objects.create(slug="acme_tenant", name="Acme")
        api_client.get("/api/v1/ping", HTTP_X_TENANT_ID="ACME_TENANT")
        assert tenant_id_var.get() == "acme_tenant"

    def test_invalid_tenant_header_returns_400(self, api_client: APIClient) -> None:
        response = api_client.get("/api/v1/ping", HTTP_X_TENANT_ID="invalid tenant id")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["error"]["code"] == "invalid_tenant"

    def test_inactive_tenant_returns_400(self, api_client: APIClient) -> None:
        Tenant.objects.create(slug="inactive", name="Inactive", is_active=False)
        response = api_client.get("/api/v1/ping", HTTP_X_TENANT_ID="inactive")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["error"]["code"] == "invalid_tenant"

    def test_unknown_tenant_returns_400(self, api_client: APIClient) -> None:
        response = api_client.get("/api/v1/ping", HTTP_X_TENANT_ID="missing")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["error"]["code"] == "invalid_tenant"


@pytest.mark.django_db
class TestItemCreateEndpoint:
    url = "/api/v1/items"

    def test_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.post(self.url, {"name": "Denied"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creates_item(self, authenticated_client: APIClient) -> None:
        payload = {"name": "Widget", "description": "A widget."}
        response = authenticated_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Widget"
        assert data["description"] == "A widget."
        assert "id" in data
        assert "created_at" in data

    def test_forbidden_without_writer_role(
        self, api_client: APIClient, django_user_model: type
    ) -> None:
        user = django_user_model.objects.create_user(username="norole", password="pass")
        api_client.force_authenticate(user=user)
        response = api_client.post(self.url, {"name": "Blocked"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_persists_to_db(self, authenticated_client: APIClient) -> None:
        authenticated_client.post(self.url, {"name": "Stored"}, format="json")
        assert Item.objects.filter(name="Stored").exists()

    def test_name_required(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.post(self.url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.json()
        assert body["error"]["code"] == "validation_error"

    def test_description_optional(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.post(self.url, {"name": "No desc"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["description"] == ""

    def test_creates_item_scoped_to_header_tenant(self, authenticated_client: APIClient) -> None:
        Tenant.objects.create(slug="acme", name="Acme")
        response = authenticated_client.post(
            self.url,
            {"name": "Tenant Widget"},
            format="json",
            HTTP_X_TENANT_ID="acme",
        )

        assert response.status_code == status.HTTP_201_CREATED
        created_item = Item.objects.get(pk=response.json()["id"])
        assert created_item.tenant.slug == "acme"


@pytest.mark.django_db
class TestItemDetailEndpoint:
    def _create_item(self) -> Item:
        public_tenant = Tenant.objects.get(slug="public")
        return Item.objects.create(name="Existing", description="desc", tenant=public_tenant)

    def test_requires_authentication(self, api_client: APIClient) -> None:
        item = self._create_item()
        response = api_client.get(f"/api/v1/items/{item.pk}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_item(self, authenticated_client: APIClient) -> None:
        item = self._create_item()
        response = authenticated_client.get(f"/api/v1/items/{item.pk}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert str(data["id"]) == str(item.pk)
        assert data["name"] == "Existing"

    def test_reader_role_can_get_item(self, api_client: APIClient, django_user_model: type) -> None:
        reader_group, _ = Group.objects.get_or_create(name=ROLE_READER)
        user = django_user_model.objects.create_user(username="reader", password="pass")
        user.groups.add(reader_group)
        api_client.force_authenticate(user=user)

        item = self._create_item()
        response = api_client.get(f"/api/v1/items/{item.pk}")
        assert response.status_code == status.HTTP_200_OK

    def test_returns_404_for_unknown_id(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.get(f"/api/v1/items/{uuid.uuid4()}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        body = response.json()
        assert body["error"]["code"] == "not_found"

    def test_returns_404_for_other_tenant_item(self, authenticated_client: APIClient) -> None:
        acme = Tenant.objects.create(slug="acme", name="Acme")
        item = Item.objects.create(name="Secret", description="", tenant=acme)

        response = authenticated_client.get(f"/api/v1/items/{item.pk}", HTTP_X_TENANT_ID="public")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"]["code"] == "not_found"


@pytest.mark.django_db
class TestAuthTokenEndpoints:
    def test_obtain_token_pair(self, api_client: APIClient, django_user_model: type) -> None:
        username = "tokenuser"
        password = "strong-pass-123"
        django_user_model.objects.create_user(username=username, password=password)

        response = api_client.post(
            "/api/v1/auth/token",
            {"username": username, "password": password},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    def test_rejects_invalid_credentials(self, api_client: APIClient) -> None:
        response = api_client.post(
            "/api/v1/auth/token",
            {"username": "missing", "password": "wrong"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_returns_new_access_token(
        self, api_client: APIClient, django_user_model: type
    ) -> None:
        username = "refreshuser"
        password = "strong-pass-123"
        django_user_model.objects.create_user(username=username, password=password)

        obtain_response = api_client.post(
            "/api/v1/auth/token",
            {"username": username, "password": password},
            format="json",
        )
        refresh_token = obtain_response.json()["refresh"]

        refresh_response = api_client.post(
            "/api/v1/auth/token/refresh",
            {"refresh": refresh_token},
            format="json",
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access" in refresh_response.json()

    def test_me_endpoint_returns_current_user(
        self,
        api_client: APIClient,
        django_user_model: type,
    ) -> None:
        username = "meuser"
        password = "strong-pass-123"
        django_user_model.objects.create_user(username=username, password=password)

        token_response = api_client.post(
            "/api/v1/auth/token",
            {"username": username, "password": password},
            format="json",
        )
        access = token_response.json()["access"]

        me_response = api_client.get(
            "/api/v1/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )

        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["username"] == username

    def test_me_endpoint_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
