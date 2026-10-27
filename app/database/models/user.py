from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, CreatedAtMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.database.models.chat import Chat
    from app.database.models.transfer import Transfer


class User(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("balance >= 0", name="balance_non_negative"),)

    email: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[str]
    balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 2),
        server_default=text("0"),
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    chats: Mapped[list["Chat"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    sent_transfers: Mapped[list["Transfer"]] = relationship(
        foreign_keys="Transfer.from_user_id",
        back_populates="from_user",
        passive_deletes="all",
        lazy="raise",
    )
    received_transfers: Mapped[list["Transfer"]] = relationship(
        foreign_keys="Transfer.to_user_id",
        back_populates="to_user",
        passive_deletes="all",
        lazy="raise",
    )
