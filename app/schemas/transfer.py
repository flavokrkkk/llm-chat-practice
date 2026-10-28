from datetime import datetime
from decimal import Decimal
from typing import NewType
from uuid import UUID

from pydantic import BaseModel, Field

from .base import BaseId, BaseSchema

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
