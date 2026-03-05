from rest_framework import serializers

from apps.accounts.models import User


class MeSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "roles"]
        read_only_fields = fields

    def get_roles(self, obj: User) -> list[str]:
        return sorted(obj.groups.values_list("name", flat=True))
