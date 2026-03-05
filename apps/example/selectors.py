import uuid

from django.db.models import QuerySet

from .models import Item


def get_item(item_id: uuid.UUID) -> Item:
    return Item.scoped.get(id=item_id)


def list_items() -> QuerySet[Item]:
    return Item.scoped.all()
