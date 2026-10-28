from datetime import datetime
from typing import NewType
from uuid import UUID

from pydantic import BaseModel, Field, Json

from .base import BaseId, BaseSchema
from .message import MessageSchema

ChatId = NewType("ChatId", BaseId)


class ChatCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ChatSchema(BaseSchema):
    id: ChatId
    user_id: UUID
    title: str
    created_at: datetime


class ChatWithMessagesSchema(BaseModel):
    id: UUID
    title: str
    user_id: UUID
    created_at: datetime
    last_messages: Json[list[MessageSchema]]
