from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.accounts.permissions import ROLE_ADMIN, ROLE_READER, ROLE_WRITER
from apps.example.models import Item


class Command(BaseCommand):
    help = "Create default API roles and assign model permissions."

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        role_to_permissions = {
            ROLE_READER: {"view_item"},
            ROLE_WRITER: {"view_item", "add_item", "change_item"},
            ROLE_ADMIN: {"view_item", "add_item", "change_item", "delete_item"},
        }

        content_type = ContentType.objects.get_for_model(Item)

        for role_name, codenames in role_to_permissions.items():
            group, created = Group.objects.get_or_create(name=role_name)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=codenames,
            )
            group.permissions.set(permissions)
            action = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"{action}: {role_name}"))

        self.stdout.write(self.style.SUCCESS("Role bootstrap complete."))
