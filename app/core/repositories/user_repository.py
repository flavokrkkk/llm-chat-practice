from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select, update

from app.core.schemas.user import TopUserStatsSchema, UserId, UserSchema
from app.infrastructure.database.models.chat import Chat
from app.infrastructure.database.models.message import Message
from app.infrastructure.database.models.user import User
from app.infrastructure.errors.exceptions import NotFoundError

from .base_repository import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository):
    async def get_user_by_id(self, user_id: UserId) -> UserSchema:

        result = await self.session.get(User, user_id)

        if result is None:
            raise NotFoundError("User not found")

        return UserSchema.model_validate(result)

    async def get_user_by_email(self, email: str) -> UserSchema:
        query = select(User).where(func.lower(User.email) == email.lower())

        result = await self.session.scalar(query)

        if result is None:
            raise NotFoundError("User not found")

        return UserSchema.model_validate(result)

    async def get_user_stats(self) -> list[TopUserStatsSchema]:
        messages_count = func.count(Message.id).label("messages_count")

        query = (
            select(
                User.id.label("user_id"),
                User.email,
                User.balance,
                User.created_at,
                messages_count,
            )
            .join(Chat, Chat.user_id == User.id)
            .join(Message, Message.chat_id == Chat.id)
            .where(Message.created_at >= func.now() - timedelta(days=7))
            .group_by(User.id)
            .order_by(messages_count.desc())
            .limit(10)
        )

        result = await self.session.execute(query)

        return [TopUserStatsSchema.model_validate(row) for row in result.mappings()]

    async def get_balance_for_update(self, user_id: UserId) -> Decimal:
        query = (
            select(User.balance)
            .where(User.id == user_id)
            .with_for_update(key_share=True)
        )

        result = await self.session.scalar(query)

        if result is None:
            raise NotFoundError("User not found")

        return result

    async def get_balance(self, user_id: UserId) -> Decimal:
        query = select(User.balance).where(User.id == user_id)

        result = await self.session.scalar(query)

        if result is None:
            raise NotFoundError("User not found")

        return result

    async def deduct_balance(self, user_id: UserId, amount: Decimal) -> None:
        query = (
            update(User)
            .where(User.id == user_id)
            .values(balance=User.balance - amount)
            .returning(User.id)
        )

        updated_id = await self.session.scalar(query)

        if updated_id is None:
            raise NotFoundError("User not found")

    async def add_balance(self, user_id: UserId, amount: Decimal) -> None:
        query = (
            update(User)
            .where(User.id == user_id)
            .values(balance=User.balance + amount)
            .returning(User.id)
        )
        updated_id = await self.session.scalar(query)

        if updated_id is None:
            raise NotFoundError("User not found")

    async def deduct_balance_atomic(self, user_id: UserId, amount: Decimal) -> bool:
        query = (
            update(User)
            .where(User.id == user_id)
            .where(User.balance >= amount)
            .values(balance=User.balance - amount)
            .returning(User.id)
        )

        updated_id = await self.session.scalar(query)

        return updated_id is not None
