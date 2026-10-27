import os
import pytest
import asyncpg
from decimal import Decimal

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://llm-chat:llm-chat@localhost:5433/llm-chat"
)

pytestmark = pytest.mark.asyncio


async def test_transfer_atomic_rollback_on_failure():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        user_id = await conn.fetchval("""
            INSERT INTO users (email, balance) 
            VALUES ('rollback_test@example.com', 1000.00) 
            RETURNING id;
            """)

        initial_balance = await conn.fetchval(
            "SELECT balance FROM users WHERE id = $1", user_id
        )
        assert initial_balance == Decimal("1000.00")

        with pytest.raises(RuntimeError):
            async with conn.transaction():
                await conn.execute(
                    "UPDATE users SET balance = balance - 100 WHERE id = $1", user_id
                )

                #  СИМУЛЯЦИЯ АВАРИИ:
                raise RuntimeError("Сервер перезагрузился!")

        balance_after_crash = await conn.fetchval(
            "SELECT balance FROM users WHERE id = $1", user_id
        )

        assert balance_after_crash == Decimal("1000.00"), (
            f"Баланс изменился на {balance_after_crash}, откат транзакции не сработал!"
        )

    finally:
        await conn.execute(
            "DELETE FROM users WHERE email = 'rollback_test@example.com'"
        )
        await conn.close()
