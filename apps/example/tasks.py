import uuid

import structlog
from celery import shared_task

from apps.example.models import Item

logger = structlog.get_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def process_item_event(self, item_id: str) -> None:  # type: ignore[no-untyped-def]
    """
    Example idempotent task:
    - If item is missing, exit cleanly.
    - If item exists, process once using immutable identifiers.
    """
    try:
        parsed_id = uuid.UUID(item_id)
    except ValueError:
        logger.warning("item_task_invalid_id", item_id=item_id)
        return

    item = Item.objects.filter(id=parsed_id).only("id").first()
    if item is None:
        logger.info("item_task_item_missing", item_id=item_id)
        return

    logger.info("item_task_processed", item_id=item_id)
