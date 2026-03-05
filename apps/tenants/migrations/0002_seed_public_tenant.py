from django.db import migrations


def seed_public_tenant(apps, schema_editor):  # noqa: ARG001
    Tenant = apps.get_model("tenants", "Tenant")
    Tenant.objects.get_or_create(
        slug="public",
        defaults={
            "name": "Public",
            "is_active": True,
        },
    )


def noop_reverse(apps, schema_editor):  # noqa: ARG001
    return


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_public_tenant, reverse_code=noop_reverse),
    ]
