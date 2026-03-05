import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.accounts.permissions import ROLE_ADMIN, ROLE_READER, ROLE_WRITER


@pytest.mark.django_db
def test_bootstrap_roles_command_creates_expected_groups() -> None:
    call_command("bootstrap_roles")

    group_names = set(Group.objects.values_list("name", flat=True))
    assert {ROLE_READER, ROLE_WRITER, ROLE_ADMIN}.issubset(group_names)
