from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.chat_service import ChatService
from app.core.services.message_service import MessageService
from app.core.services.transfer_service import TransferService
from app.core.services.user_service import UserService
from app.infrastructure.redis.cache import RedisCache


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.db_connection.session_factory() as session:
        yield session


def get_cache(request: Request) -> RedisCache:
    return request.app.state.cache


def get_redis(request: Request) -> Redis:
    return request.app.state.redis_connection.redis


SessionDep = Annotated[AsyncSession, Depends(get_session)]
CacheDep = Annotated[RedisCache, Depends(get_cache)]


def get_chat_service(session: SessionDep) -> ChatService:
    """Функция для инъекции зависимости ChatService"""

    return ChatService(session)


def get_message_service(
    session: SessionDep,
) -> MessageService:
    """Функция для инъекции зависимости MessageService"""

    return MessageService(session)


def get_user_service(
    session: SessionDep,
    cache: CacheDep,
) -> UserService:
    """Функция для инъекции зависимости UserService"""

    return UserService(session, cache)


def get_transfer_service(
    session: SessionDep,
) -> TransferService:
    """Функция для инъекции зависимости TransferService"""

    return TransferService(session)
