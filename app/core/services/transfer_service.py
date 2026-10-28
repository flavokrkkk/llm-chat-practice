import asyncio
from decimal import Decimal

import asyncpg

from app.core.decorator import retry_on_transient_db_error
from app.core.repositories.transfer_repository import TransferRepository
from app.core.repositories.user_repository import UserRepository
from app.core.schemas.transfer import TransferSchema
from app.core.schemas.user import UserId
from app.infrastructure.errors.exceptions import InsufficientFundsError


class TransferService:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        self.transfer_repository = TransferRepository(connection)
        self.user_repository = UserRepository(connection)

    async def transfer_for_update(
        self, from_user_id: UserId, to_user_id: UserId, amount: Decimal
    ) -> TransferSchema:

        async with self.connection.transaction():
            balance = await self.user_repository.get_balance_for_update(from_user_id)

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

            transfer = await self.transfer_repository.create_transfer(
                to_user_id, from_user_id, amount
            )

            return transfer

    async def transfer_atomic_update(
        self, from_user_id: UserId, to_user_id: UserId, amount: Decimal
    ) -> TransferSchema:
        async with self.connection.transaction():
            success = await self.user_repository.deduct_balance_atomic(
                from_user_id, amount
            )

            if not success:
                raise InsufficientFundsError("Недостаточно средств")

            await self.user_repository.add_balance(to_user_id, amount)

            return await self.transfer_repository.create_transfer(
                to_user_id, from_user_id, amount
            )

    @retry_on_transient_db_error(max_retries=15, delay=0.02)
    async def transfer_serializable_update(
        self, from_user_id: UserId, to_user_id: UserId, amount: Decimal
    ) -> TransferSchema:
        async with self.connection.transaction(isolation="serializable"):
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

            transfer = await self.transfer_repository.create_transfer(
                to_user_id, from_user_id, amount
            )

            return transfer

    async def transfer_deadlock_prone(
        self, from_user_id: UserId, to_user_id: UserId, amount: Decimal
    ) -> TransferSchema:
        async with self.connection.transaction():
            await self.user_repository.get_balance_for_update(from_user_id)

            await asyncio.sleep(0.1)

            await self.user_repository.get_balance_for_update(to_user_id)

            await self.user_repository.deduct_balance(from_user_id, amount)

            await self.user_repository.add_balance(to_user_id, amount)

            return await self.transfer_repository.create_transfer(
                to_user_id, from_user_id, amount
            )

    async def transfer_deadlock_free(
        self, from_user_id: UserId, to_user_id: UserId, amount: Decimal
    ) -> TransferSchema:
        first_id, second_id = sorted([from_user_id, to_user_id])

        async with self.connection.transaction():
            await self.user_repository.get_balance_for_update(first_id)

            await asyncio.sleep(0.1)

            await self.user_repository.get_balance_for_update(second_id)

            from_user_balance = await self.user_repository.get_balance(from_user_id)
            if from_user_balance < amount:
                raise InsufficientFundsError(
                    f"Недостаточно средств: {from_user_balance} < {amount}"
                )

            await self.user_repository.deduct_balance(from_user_id, amount)
            await self.user_repository.add_balance(to_user_id, amount)

            return await self.transfer_repository.create_transfer(
                to_user_id, from_user_id, amount
            )
