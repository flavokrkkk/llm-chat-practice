from fastapi import APIRouter, Depends, Query
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.api.dependencies.dependencies import get_user_service, get_chat_service
from pydantic import EmailStr
from app.schemas.user import UserId

router = APIRouter()


@router.get("/by-email")
async def get_chat_by_id(
    email: EmailStr = Query(..., description="Электронная почта пользователя"),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_user_by_email(email)


@router.get("/{user_id}/chats")
async def get_user_chats(
    user_id: UserId,
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.get_user_chats(user_id)
