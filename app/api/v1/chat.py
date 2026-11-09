from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query

from app.api.dependencies.dependencies import (
    CurrentUserDep,
    get_chat_service,
    get_message_service,
)
from app.api.dependencies.rate_limiter import limit_messages
from app.core.schemas.chat import ChatCreate, ChatId
from app.core.schemas.message import MessageCreate
from app.core.services.chat_service import ChatService
from app.core.services.message_service import MessageService

router = APIRouter()


@router.get("/{chat_id}")
async def get_chat_by_id(
    current_user: CurrentUserDep,
    chat_id: ChatId,
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.get_chat_by_id(chat_id=chat_id, user_id=current_user.id)


@router.post("", status_code=201)
async def create_chat(
    chat_dto: ChatCreate,
    current_user: CurrentUserDep,
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.create_chat(user_id=current_user.id, title=chat_dto.title)


@router.get("/{chat_id}/messages")
async def get_chat_messages(
    chat_id: ChatId,
    current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=100),
    message_service: MessageService = Depends(get_message_service),
):
    return await message_service.get_chat_messages(
        user_id=current_user.id, chat_id=chat_id, limit=limit
    )


@router.get("/{chat_id}/messages/offset")
async def get_chat_messages_offset(
    chat_id: ChatId,
    current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
    message_service: MessageService = Depends(get_message_service),
):
    return await message_service.get_chat_messages_offset(
        user_id=current_user.id, chat_id=chat_id, limit=limit, offset=offset
    )


@router.get("/{chat_id}/messages/keyset")
async def get_chat_messages_keyset(
    chat_id: ChatId,
    current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=100),
    cursor_id: UUID | None = Query(default=None),
    cursor_created_at: datetime | None = Query(default=None),
    message_service: MessageService = Depends(get_message_service),
):
    return await message_service.get_chat_messages_keyset(
        user_id=current_user.id,
        chat_id=chat_id,
        limit=limit,
        cursor_id=cursor_id,
        cursor_created_at=cursor_created_at,
    )


@router.post(
    "/{chat_id}/messages",
    dependencies=[Depends(limit_messages)],
    status_code=201,
)
async def create_chat_message(
    current_user: CurrentUserDep,
    chat_id: ChatId,
    message_dto: MessageCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    message_service: MessageService = Depends(get_message_service),
):
    return await message_service.create_chat_message(
        chat_id=chat_id,
        user_id=current_user.id,
        content=message_dto.content,
        idempotency_key=idempotency_key,
    )
