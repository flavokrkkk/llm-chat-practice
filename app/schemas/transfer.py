from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from .base import BaseSchema, BaseId
from decimal import Decimal
from typing import NewType

TransferId = NewType("TransferId", BaseId)


class TransferCreate(BaseModel):
    to_user_id: UUID
    from_user_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class TransferSchema(BaseSchema):
    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    amount: Decimal
    created_at: datetime
