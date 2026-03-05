from rest_framework.permissions import BasePermission

ROLE_ADMIN = "api_admin"
ROLE_WRITER = "api_writer"
ROLE_READER = "api_reader"
DEFAULT_ROLES: tuple[str, ...] = (ROLE_READER, ROLE_WRITER, ROLE_ADMIN)


class HasAnyRole(BasePermission):
    message = "You do not have the required role for this operation."

    def has_permission(self, request, view) -> bool:  # type: ignore[no-untyped-def]
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        allowed_roles = getattr(view, "allowed_roles", DEFAULT_ROLES)
        if not allowed_roles:
            return True

        return user.groups.filter(name__in=allowed_roles).exists()
