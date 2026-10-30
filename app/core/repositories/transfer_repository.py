from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert

from app.core.schemas.transfer import TransferSchema
from app.core.schemas.user import UserId
from app.infrastructure.database.models.transfer import Transfer

from .base_repository import SqlAlchemyRepository


class TransferRepository(SqlAlchemyRepository):
    async def create_transfer(
        self, from_user_id: UserId, to_user_id: UserId, amount: Decimal
    ) -> TransferSchema:

        query = (
            insert(Transfer)
            .on_conflict_do_nothing(index_elements=[Transfer.idempotency_key])
            .values(from_user_id=from_user_id, to_user_id=to_user_id, amount=amount)
            .returning(Transfer)
        )

        row = await self.session.scalar(query)

        return TransferSchema.model_validate(row)
