import pytest
from django.core.exceptions import ValidationError

from apps.example.models import Item
from apps.example.services import create_item
from apps.tenants.models import Tenant
from config.context import tenant_id_var


@pytest.mark.django_db
class TestCreateItem:
    @pytest.fixture(autouse=True)
    def _ensure_public_tenant(self) -> None:
        Tenant.objects.get_or_create(slug="public", defaults={"name": "Public", "is_active": True})

    def test_creates_item_with_name(self) -> None:
        item = create_item(name="Widget")
        assert item.pk is not None
        assert item.name == "Widget"
        assert item.description == ""
        assert item.tenant.slug == "public"
        assert Item.objects.filter(pk=item.pk).exists()

    def test_creates_item_with_description(self) -> None:
        item = create_item(name="Widget", description="A useful widget.")
        assert item.description == "A useful widget."

    def test_persists_to_database(self) -> None:
        item = create_item(name="Persisted")
        fetched = Item.objects.get(pk=item.pk)
        assert fetched.name == "Persisted"
        assert fetched.tenant.slug == "public"

    def test_uses_tenant_from_context(self) -> None:
        Tenant.objects.create(slug="acme", name="Acme")
        token = tenant_id_var.set("acme")
        try:
            item = create_item(name="Tenant bound")
        finally:
            tenant_id_var.reset(token)

        assert item.tenant.slug == "acme"

    def test_raises_on_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            create_item(name="")

    def test_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            create_item(name="x" * 256)
