from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from .base import BaseSchema


class UserCreate(BaseModel):
    email: EmailStr
    balance: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


class UserResponse(BaseSchema):
    id: UUID
    email: EmailStr
    balance: Decimal
    created_at: datetime
