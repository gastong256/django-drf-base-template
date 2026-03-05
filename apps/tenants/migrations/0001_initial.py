import uuid

from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "slug",
                    models.CharField(
                        max_length=63,
                        unique=True,
                        validators=[
                            RegexValidator(
                                message="Tenant slug must contain only lowercase letters, numbers, underscores, or hyphens.",
                                regex="^[a-z0-9][a-z0-9_-]{0,62}$",
                            )
                        ],
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["slug"]},
        )
    ]
