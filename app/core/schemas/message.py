from datetime import datetime
from enum import Enum
from typing import NewType
from uuid import UUID

from pydantic import BaseModel, Field

from .base import BaseId, BaseSchema

MessageId = NewType("MessageId", BaseId)


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


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
