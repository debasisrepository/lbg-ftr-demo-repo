from contextvars import ContextVar
from typing import Optional
import uuid


correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class RequestContext:
    @staticmethod
    def get_correlation_id() -> str:
        cid = correlation_id_var.get()
        if not cid:
            cid = str(uuid.uuid4())
            correlation_id_var.set(cid)
        return cid

    @staticmethod
    def set_correlation_id(value: str) -> None:
        correlation_id_var.set(value)
