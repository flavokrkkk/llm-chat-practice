from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, CreatedAtMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.database.models.user import User


class Transfer(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("from_user_id <> to_user_id", name="different_users"),
    )

    from_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    to_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(19, 2),
    )

    from_user: Mapped["User"] = relationship(
        foreign_keys=[from_user_id], back_populates="sent_transfers"
    )
    to_user: Mapped["User"] = relationship(
        foreign_keys=[to_user_id], back_populates="received_transfers"
    )
