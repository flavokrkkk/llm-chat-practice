from fastapi import APIRouter, Depends, Query
from app.services.chat_service import ChatService
from app.services.message_service import MessageService
from app.schemas.chat import ChatId
from app.api.dependencies import get_chat_service, get_message_service
from datetime import datetime
from uuid import UUID

router = APIRouter()


@router.get("/{chat_id}")
async def get_chat_by_id(
    chat_id: ChatId, chat_service: ChatService = Depends(get_chat_service)
):
    return await chat_service.get_chat_by_id(chat_id)


@router.get("/{chat_id}/messages")
async def get_chat_messages(
    chat_id: ChatId,
    limit: int = Query(default=50, ge=1, le=100),
    message_service: MessageService = Depends(get_message_service),
):
    return await message_service.get_chat_messages(chat_id, limit)


@router.get("/{chat_id}/messages/offset")
async def get_chat_messages_offset(
    chat_id: ChatId,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=50, ge=0, le=100),
    message_service: MessageService = Depends(get_message_service),
):
    return await message_service.get_chat_messages_offset(chat_id, limit, offset)


@router.get("/{chat_id}/messages/keyset")
async def get_chat_messages_keyset(
    chat_id: ChatId,
    limit: int = Query(default=50, ge=1, le=100),
    cursor_id: UUID | None = Query(default=None),
    cursor_created_at: datetime | None = Query(default=None),
    message_service: MessageService = Depends(get_message_service),
):
    return await message_service.get_chat_messages_keyset(
        chat_id, limit, cursor_id=cursor_id, cursor_created_at=cursor_created_at
    )
