from datetime import datetime
from typing import Any
from uuid import UUID

from utils.enums import PendingActionKind, PendingActionStatus

from .base import BaseSchema


class PendingActionSchema(BaseSchema):
    id: UUID
    chat_id: UUID
    user_id: UUID
    tool_call_id: str
    kind: PendingActionKind
    status: PendingActionStatus
    payload: dict[str, Any]
    expires_at: datetime
    resolved_at: datetime
