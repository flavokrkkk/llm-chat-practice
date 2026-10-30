from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import (
    Base,
    CreatedAtMixin,
    UUIDPkMixin,
    str_enum,
)
from app.utils.enums import PendingActionKind, PendingActionStatus

if TYPE_CHECKING:
    from app.infrastructure.database.models.chat import Chat
    from app.infrastructure.database.models.user import User


class PendingAction(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "pending_actions"
    __table_args__ = (
        Index(
            "ix_pending_actions_chat_id_pending",
            "chat_id",
            postgresql_where=text("status = 'pending'"),
        ),
        Index(
            "ix_pending_actions_expires_at_pending",
            "expires_at",
            postgresql_where=text("status = 'pending'"),
        ),
    )

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    tool_call_id: Mapped[str] = mapped_column(String(255), unique=True)
    kind: Mapped[PendingActionKind] = mapped_column(
        str_enum(PendingActionKind, name="kind", length=32)
    )
    status: Mapped[PendingActionStatus] = mapped_column(
        str_enum(PendingActionStatus, name="status", length=10),
        server_default="pending",
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    chat: Mapped["Chat"] = relationship(
        back_populates="pending_actions",
        lazy="raise",
    )
    user: Mapped["User"] = relationship(back_populates="pending_actions", lazy="raise")
