from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from .base import BaseSchema
from decimal import Decimal


class TransferCreate(BaseModel):
    to_user_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class TransferResponse(BaseSchema):
    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    amount: Decimal
    created_at: datetime
