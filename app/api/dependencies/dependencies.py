import asyncpg
from fastapi import Depends

from app.core.clients.redis_client import RedisClient, get_redis
from app.core.services.chat_service import ChatService
from app.core.services.message_service import MessageService
from app.core.services.transfer_service import TransferService
from app.core.services.user_service import UserService
from app.infrastructure.database.connection.postgres_connection import database


def get_chat_service(connection: asyncpg.Connection = Depends(database.get_connection)):
    """Функция для инъекции зависимости ChatService"""

    return ChatService(connection)


def get_message_service(
    connection: asyncpg.Connection = Depends(database.get_connection),
):
    """Функция для инъекции зависимости MessageService"""

    return MessageService(connection)


def get_user_service(
    connection: asyncpg.Connection = Depends(database.get_connection),
    redis_client: RedisClient = Depends(get_redis),
):
    """Функция для инъекции зависимости UserService"""

    return UserService(connection, redis_client)


def get_transfer_service(
    connection: asyncpg.Connection = Depends(database.get_connection),
):
    """Функция для инъекции зависимости TransferService"""

    return TransferService(connection)
