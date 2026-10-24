from pydantic import BaseModel, Field
from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import NewType
from .base import BaseSchema, BaseId

MessageId = NewType("MessageId", BaseId)


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageCreate(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1)
    idempotency_key: str | None = Field(default=None, max_length=255)


class MessageSchema(BaseSchema):
    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    idempotency_key: str | None
    created_at: datetime
