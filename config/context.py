import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="public")
tenant_pk_var: ContextVar[uuid.UUID | None] = ContextVar("tenant_pk", default=None)
