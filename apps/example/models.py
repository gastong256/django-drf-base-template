import uuid

from django.db import models

from apps.tenants.models import TenantOwnedModel


class Item(TenantOwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "-created_at"], name="ex_item_tenant_created_idx"),
        ]

    def __str__(self) -> str:
        return self.name
