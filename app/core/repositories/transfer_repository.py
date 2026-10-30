from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert

from app.core.schemas.base import CursorPaginationResponse
from app.core.schemas.transfer import TransferSchema
from app.core.schemas.user import UserId
from app.infrastructure.database.models.transfer import Transfer

from .base_repository import SqlAlchemyRepository


class TransferRepository(SqlAlchemyRepository):
    async def create_transfer(
        self,
        from_user_id: UserId,
        to_user_id: UserId,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferSchema | None:

        query = (
            insert(Transfer)
            .values(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )
            .on_conflict_do_nothing(index_elements=[Transfer.idempotency_key])
            .returning(Transfer)
        )

        row = await self.session.scalar(query)

        return TransferSchema.model_validate(row) if row is not None else None

    async def get_transfer_by_idempotency_key(
        self, idempotency_key: str
    ) -> TransferSchema | None:
        query = select(Transfer).where(Transfer.idempotency_key == idempotency_key)

        result = await self.session.scalar(query)

        return TransferSchema.model_validate(result) if result is not None else None

    async def get_transfer_history_keyset(
        self,
        user_id: UserId,
        limit: int,
        cursor_id: UUID | None = None,
        cursor_created_at: datetime | None = None,
    ) -> CursorPaginationResponse:

        final_query = (
            select(Transfer)
            .where(
                or_(Transfer.from_user_id == user_id, Transfer.to_user_id == user_id)
            )
            .order_by(Transfer.created_at.desc(), Transfer.id.desc())
            .limit(limit + 1)
        )

        if cursor_id is not None and cursor_created_at is not None:
            final_query = final_query.where(
                tuple_(Transfer.created_at, Transfer.id)
                < tuple_(cursor_created_at, cursor_id)
            )

        rows = (await self.session.scalars(final_query)).all()

        has_more = len(rows) > limit

        items = [TransferSchema.model_validate(x) for x in rows[:limit]]

        next_created_at = None
        next_id = None

        if has_more:
            next_created_at = items[-1].created_at
            next_id = items[-1].id

        return CursorPaginationResponse(
            items=items,
            next_created_at=next_created_at,
            next_id=next_id,
            limit=limit,
        )
