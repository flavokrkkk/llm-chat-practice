from fastapi import APIRouter, Depends, Header

from app.api.dependencies.dependencies import get_transfer_service
from app.core.schemas.transfer import TransferCreate
from app.core.services.transfer_service import TransferService

router = APIRouter()


@router.post("")
async def create_transfer(
    transfer_dto: TransferCreate,
    transfer_service: TransferService = Depends(get_transfer_service),
    idempotency_key: str = Header(
        alias="Idempotency-Key", max_length=255, min_length=1
    ),
):
    return await transfer_service.transfer_deadlock_free(
        to_user_id=transfer_dto.to_user_id,
        from_user_id=transfer_dto.from_user_id,
        amount=transfer_dto.amount,
        idempotency_key=idempotency_key,
    )
