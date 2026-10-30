from datetime import datetime
from typing import NewType
from uuid import UUID

from pydantic import BaseModel, Field

from app.utils.enums import MessageRole

from .base import BaseId, BaseSchema

MessageId = NewType("MessageId", BaseId)


class MessageCreate(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1)


class MessageSchema(BaseSchema):
    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    idempotency_key: str | None
    created_at: datetime
