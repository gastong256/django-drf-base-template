from typing import Any, cast

from apps.tenants.models import Tenant
from config.context import tenant_id_var, tenant_pk_var

from .models import Item


def create_item(*, name: str, description: str = "") -> Item:
    tenant_pk = tenant_pk_var.get()
    if tenant_pk is None:
        tenant_model = cast(Any, Tenant)
        tenant_pk = tenant_model.objects.only("id").get(slug=tenant_id_var.get(), is_active=True).pk

    item = Item(name=name, description=description, tenant_id=tenant_pk)
    item.full_clean()
    item.save()
    return item
