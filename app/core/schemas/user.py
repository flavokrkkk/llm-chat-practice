from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .base import BaseSchema


class UserCreate(BaseModel):
    email: EmailStr
    balance: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


class UserSchema(BaseSchema):
    id: UUID
    email: EmailStr
    balance: Decimal
    created_at: datetime
    is_active: bool


class UserSchemaWithCredentials(BaseSchema):
    id: UUID
    email: EmailStr
    balance: Decimal
    created_at: datetime
    password_hash: str
    is_active: bool


class TopUserStatsSchema(BaseSchema):
    user_id: UUID
    email: EmailStr
    balance: Decimal
    created_at: datetime
    messages_count: int = Field(
        ..., ge=0, description="Количество сообщений за последние 7 дней"
    )
