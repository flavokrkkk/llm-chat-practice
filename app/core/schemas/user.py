from datetime import datetime
from decimal import Decimal
from typing import NewType
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .base import BaseId, BaseSchema

UserId = NewType("UserId", BaseId)


class UserCreate(BaseModel):
    email: EmailStr
    balance: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


class UserSchema(BaseSchema):
    id: UUID
    email: EmailStr
    balance: Decimal
    created_at: datetime


class TopUserStatsSchema(BaseSchema):
    user_id: UUID
    email: EmailStr
    balance: Decimal
    created_at: datetime
    messages_count: int = Field(
        ..., ge=0, description="Количество сообщений за последние 7 дней"
    )
