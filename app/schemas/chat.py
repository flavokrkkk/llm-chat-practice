from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import NewType
from .base import BaseSchema, BaseId

ChatId = NewType("ChatId", BaseId)


class ChatCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ChatSchema(BaseSchema):
    id: ChatId
    user_id: UUID
    title: str
    created_at: datetime
