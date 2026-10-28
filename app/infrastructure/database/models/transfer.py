from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, CreatedAtMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.user import User


class Transfer(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "transfers"
    __table_args__ = (
        Index(
            "ix_transfers_from_user_id_created_at_id",
            "from_user_id",
            "created_at",
            "id",
        ),
        Index(
            "ix_transfers_to_user_id_created_at_id", "to_user_id", "created_at", "id"
        ),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("from_user_id <> to_user_id", name="different_users"),
    )

    from_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    to_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(19, 2),
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)

    from_user: Mapped["User"] = relationship(
        foreign_keys=[from_user_id], back_populates="sent_transfers"
    )
    to_user: Mapped["User"] = relationship(
        foreign_keys=[to_user_id], back_populates="received_transfers"
    )
