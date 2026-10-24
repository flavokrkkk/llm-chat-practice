from fastapi import APIRouter, Depends, Query
from app.services.user_service import UserService
from app.api.dependencies import get_user_service
from pydantic import EmailStr

router = APIRouter()


@router.get("/by-email")
async def get_chat_by_id(
    email: EmailStr = Query(..., description="Электронная почта пользователя"),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_user_by_email(email)
