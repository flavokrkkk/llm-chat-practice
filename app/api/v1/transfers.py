from fastapi import APIRouter, Depends
from app.services.transfer_service import TransferService
from app.api.dependencies import get_transfer_service
from app.schemas.transfer import TransferCreate

router = APIRouter()


@router.post("/")
async def create_transfer(
    transfer_dto: TransferCreate,
    transfer_service: TransferService = Depends(get_transfer_service),
):
    return await transfer_service.transfer_deadlock_free(
        to_user_id=transfer_dto.to_user_id,
        from_user_id=transfer_dto.from_user_id,
        amount=transfer_dto.amount,
    )
