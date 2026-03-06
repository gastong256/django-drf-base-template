import uuid

from django.core.validators import RegexValidator
from django.db import models

from config.context import tenant_id_var

tenant_slug_validator = RegexValidator(
    regex=r"^[a-z0-9][a-z0-9_-]{0,62}$",
    message="Tenant slug must contain only lowercase letters, numbers, underscores, or hyphens.",
)


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.CharField(
        max_length=63,
        unique=True,
        validators=[tenant_slug_validator],
    )
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)  # pyright: ignore[reportArgumentType]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self) -> str:
        return str(self.slug)


class TenantScopedQuerySet(models.QuerySet):
    def for_tenant(self, tenant_slug: str) -> "TenantScopedQuerySet":
        return self.filter(tenant__slug=tenant_slug)

    def for_current_tenant(self) -> "TenantScopedQuerySet":
        return self.for_tenant(tenant_id_var.get())


class TenantScopedManager(models.Manager):
    def get_queryset(self) -> TenantScopedQuerySet:
        queryset = TenantScopedQuerySet(self.model, using=self._db)
        return queryset.for_current_tenant()


class TenantOwnedModel(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_set",
    )

    objects = models.Manager()
    scoped = TenantScopedManager()

    class Meta:
        abstract = True
