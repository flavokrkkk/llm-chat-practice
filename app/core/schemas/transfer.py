from datetime import datetime
from decimal import Decimal
from typing import NewType

from pydantic import BaseModel, Field

from .base import BaseId, BaseSchema
from .user import UserId

TransferId = NewType("TransferId", BaseId)


class TransferCreate(BaseModel):
    to_user_id: UserId
    from_user_id: UserId
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class TransferSchema(BaseSchema):
    id: UserId
    from_user_id: UserId
    to_user_id: UserId
    amount: Decimal
    created_at: datetime
