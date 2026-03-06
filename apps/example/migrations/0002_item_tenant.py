import django.db.models.deletion
from django.db import migrations, models


def assign_public_tenant(apps, schema_editor):  # noqa: ARG001
    Tenant = apps.get_model("tenants", "Tenant")
    Item = apps.get_model("example", "Item")
    public_tenant = Tenant.objects.get(slug="public")
    Item.objects.filter(tenant__isnull=True).update(tenant=public_tenant)


def noop_reverse(apps, schema_editor):  # noqa: ARG001
    return


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0002_seed_public_tenant"),
        ("example", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="tenant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.RunPython(assign_public_tenant, reverse_code=noop_reverse),
        migrations.AlterField(
            model_name="item",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AddIndex(
            model_name="item",
            index=models.Index(fields=["tenant", "-created_at"], name="ex_item_tenant_created_idx"),
        ),
    ]
