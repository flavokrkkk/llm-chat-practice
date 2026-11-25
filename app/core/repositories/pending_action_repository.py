from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from utils.enums import PendingActionKind, PendingActionStatus

from app.core.schemas.pending_action import PendingActionSchema
from app.infrastructure.database.models.pending_action import PendingAction

from .base_repository import SqlAlchemyRepository


class PendingActionRepository(SqlAlchemyRepository):
    async def find_by_tool_call_id(
        self, chat_id: UUID, tool_call_id: str
    ) -> PendingActionSchema | None:
        query = select(PendingAction).where(
            PendingAction.chat_id == chat_id, PendingAction.tool_call_id == tool_call_id
        )

        row = await self.session.scalar(query)

        return PendingActionSchema.model_validate(row) if row is not None else None

    async def create_or_get(
        self,
        tool_call_id: str,
        chat_id: UUID,
        user_id: UUID,
        kind: PendingActionKind,
        payload: dict[str, Any],
        ttl_seconds: float,
    ) -> tuple[PendingActionSchema, bool]:
        query = (
            insert(PendingAction)
            .values(
                tool_call_id=tool_call_id,
                user_id=user_id,
                chat_id=chat_id,
                kind=kind,
                payload=payload,
                expires_at=func.now() + timedelta(seconds=ttl_seconds),
            )
            .on_conflict_do_nothing(
                index_elements=[PendingAction.chat_id, PendingAction.tool_call_id]
            )
            .returning(PendingAction)
        )

        row = (await self.session.execute(query)).scalar_one_or_none()

        # нет конфликта, вернули создавшееся
        if row is not None:
            return PendingActionSchema.model_validate(row), True

        existing = await self.find_by_tool_call_id(chat_id, tool_call_id)

        if existing is None:
            raise RuntimeError("Pending action conflict, but row not found")

        if existing.user_id != user_id:
            raise RuntimeError("Pending action belongs to another user")

        if existing.payload != payload:
            raise RuntimeError("Pending action payload mismatch")

        return existing, False

    async def change_status(
        self,
        action_id: UUID,
        user_id: UUID,
        decision: PendingActionStatus,
    ) -> PendingActionSchema | None:
        query = (
            update(PendingAction)
            .where(
                PendingAction.id == action_id,
                PendingAction.user_id == user_id,
                PendingAction.expires_at > func.now(),
                PendingAction.status == PendingActionStatus.PENDING,
            )
            .values(status=decision, resolved_at=func.now())
        ).returning(PendingAction)

        row = (await self.session.execute(query)).scalar_one_or_none()

        return PendingActionSchema.model_validate(row) if row is not None else None
