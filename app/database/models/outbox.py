import enum
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Identity, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, CreatedAtMixin, str_enum


class OutboxEventType(enum.StrEnum):
    TRANSFER_COMPLETED = "transfer.completed"


class Outbox(CreatedAtMixin, Base):
    __tablename__ = "outbox"
    __table_args__ = (
        Index(
            "ix_outbox_id_unprocessed",
            "id",
            postgresql_where=text("processed_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    event_type: Mapped[OutboxEventType] = mapped_column(
        str_enum(OutboxEventType, name="event_type", length=64)
    )
    attempts: Mapped[int] = mapped_column(server_default=text("0"))
    last_error: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
