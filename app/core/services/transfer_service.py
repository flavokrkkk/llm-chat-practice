import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorator import retry_on_transient_db_error
from app.core.repositories.transfer_repository import TransferRepository
from app.core.repositories.user_repository import UserRepository
from app.core.schemas.transfer import TransferSchema
from app.core.schemas.user import UserId
from app.infrastructure.errors.exceptions import (
    ConflictError,
    InsufficientFundsError,
)


class TransferService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transfer_repository = TransferRepository(session)
        self.user_repository = UserRepository(session)

    async def _create_or_get_existing(
        self,
        from_user_id: UserId,
        to_user_id: UserId,
        amount: Decimal,
        idempotency_key: str,
    ) -> tuple[TransferSchema, bool]:
        transfer = await self.transfer_repository.create_transfer(
            to_user_id=to_user_id,
            from_user_id=from_user_id,
            amount=amount,
            idempotency_key=idempotency_key,
        )

        if transfer is None:
            existing = await self.transfer_repository.get_transfer_by_idempotency_key(
                idempotency_key=idempotency_key
            )

            if existing is None:
                raise RuntimeError("Использован некорректный ключ операции")
            if not (
                existing.from_user_id == from_user_id
                and existing.to_user_id == to_user_id
                and existing.amount == amount
            ):
                raise ConflictError("Параметры операции не совпадают")

            return (existing, True)

        return (transfer, False)

    async def transfer_for_update(
        self,
        from_user_id: UserId,
        to_user_id: UserId,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferSchema:

        async with self.session.begin():
            transfer, already_existed = await self._create_or_get_existing(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )

            if already_existed:
                return transfer

            balance = await self.user_repository.get_balance_for_update(from_user_id)

            if balance < amount:
                raise InsufficientFundsError(
                    f"Недостаточно средств: {balance} < {amount}"
                )

            await self.user_repository.deduct_balance(
                amount=amount, user_id=from_user_id
            )

            await self.user_repository.add_balance(
                amount=amount,
                user_id=to_user_id,
            )

            return transfer

    async def transfer_atomic_update(
        self,
        from_user_id: UserId,
        to_user_id: UserId,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferSchema:
        async with self.session.begin():
            transfer, already_existed = await self._create_or_get_existing(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )

            if already_existed:
                return transfer

            success = await self.user_repository.deduct_balance_atomic(
                from_user_id, amount
            )

            if not success:
                raise InsufficientFundsError("Недостаточно средств")

            await self.user_repository.add_balance(to_user_id, amount)

            return transfer

    @retry_on_transient_db_error(max_attempts=15, delay=0.02)
    async def transfer_serializable_update(
        self,
        from_user_id: UserId,
        to_user_id: UserId,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferSchema:
        await self.session.connection(
            execution_options={"isolation_level": "SERIALIZABLE"}
        )
        async with self.session.begin():
            transfer, already_existed = await self._create_or_get_existing(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )

            if already_existed:
                return transfer

            balance = await self.user_repository.get_balance(from_user_id)

            if balance < amount:
                raise InsufficientFundsError(
                    f"Недостаточно средств: {balance} < {amount}"
                )

            await asyncio.sleep(0.05)

            await self.user_repository.deduct_balance(
                amount=amount, user_id=from_user_id
            )

            await self.user_repository.add_balance(
                amount=amount,
                user_id=to_user_id,
            )

            return transfer

    async def transfer_deadlock_prone(
        self,
        from_user_id: UserId,
        to_user_id: UserId,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferSchema:
        async with self.session.begin():
            transfer, already_existed = await self._create_or_get_existing(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )

            if already_existed:
                return transfer

            await self.user_repository.get_balance_for_update(from_user_id)

            await self.user_repository.get_balance_for_update(to_user_id)

            await self.user_repository.deduct_balance(from_user_id, amount)

            await self.user_repository.add_balance(to_user_id, amount)

            return transfer

    async def transfer_deadlock_free(
        self,
        from_user_id: UserId,
        to_user_id: UserId,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferSchema:
        first_id, second_id = sorted([from_user_id, to_user_id])

        async with self.session.begin():
            transfer, already_existed = await self._create_or_get_existing(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )

            if already_existed:
                return transfer

            await self.user_repository.get_balance_for_update(first_id)

            await self.user_repository.get_balance_for_update(second_id)

            from_user_balance = await self.user_repository.get_balance(from_user_id)
            if from_user_balance < amount:
                raise InsufficientFundsError(
                    f"Недостаточно средств: {from_user_balance} < {amount}"
                )

            await self.user_repository.deduct_balance(from_user_id, amount)
            await self.user_repository.add_balance(to_user_id, amount)

            return transfer
