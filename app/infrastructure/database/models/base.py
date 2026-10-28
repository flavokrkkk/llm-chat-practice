import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, MetaData, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UUIDPkMixin:
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


def _enum_values(enum_cls: type[enum.StrEnum]) -> list[str]:
    return [m.value for m in enum_cls]


def str_enum(enum_cls: type[enum.StrEnum], *, name: str, length: int) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        length=length,
        native_enum=False,
        create_constraint=True,
        values_callable=_enum_values,
    )


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    __mapper_args__ = {"eager_defaults": True}
