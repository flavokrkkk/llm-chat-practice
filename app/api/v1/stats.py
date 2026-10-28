from fastapi import APIRouter, Depends

from app.api.dependencies.dependencies import get_user_service
from app.core.services.user_service import UserService

router = APIRouter()


@router.get("/top-users")
async def get_top_users(user_service: UserService = Depends(get_user_service)):
    return await user_service.get_user_stats()
