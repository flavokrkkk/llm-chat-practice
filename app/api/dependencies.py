import asyncpg
from fastapi import Depends
from app.database.connection.postgres_connection import database
from app.services.chat_service import ChatService
from app.services.message_service import MessageService
from app.services.user_service import UserService
from app.services.transfer_service import TransferService


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
):
    """Функция для инъекции зависимости UserService"""

    return UserService(connection)


def get_transfer_service(
    connection: asyncpg.Connection = Depends(database.get_connection),
):
    """Функция для инъекции зависимости TransferService"""

    return TransferService(connection)
