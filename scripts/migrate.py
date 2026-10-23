import os
import sys
import asyncio
from pathlib import Path
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL")

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

MIGRATION_LOCK_ID = 123456789


async def run_migrations():
    if not DATABASE_URL:
        print("DATABASE_URL is not set!")
        sys.exit(1)

    conn = await asyncpg.connect(DATABASE_URL)
    lock_acquired = False

    try:

        print("Acquiring migration lock...")

        await conn.execute("SELECT pg_advisory_lock($1);", MIGRATION_LOCK_ID)
        lock_acquired = True

        print("Lock acquired!")

        await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

        applied = {
            x["name"] for x in await conn.fetch("SELECT name FROM schema_migrations")
        }

        files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        if not files:
            print("No migration files found.")
            return

        for file_path in files:
            filename = file_path.name

            if filename in applied:
                continue

            print(f"Applying migration: {filename}...")

            with open(file_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            try:

                async with conn.transaction():
                    await conn.execute(sql_content)
                    await conn.execute(
                        "INSERT INTO schema_migrations (name) VALUES ($1);",
                        filename,
                    )
                print(f"Successfully applied: {filename}")
            except Exception as e:
                print(f"Failed to apply {filename}: {e}")
                raise e

        print("All migrations are up to date.")

    finally:
        if lock_acquired:
            await conn.execute("SELECT pg_advisory_unlock($1);", MIGRATION_LOCK_ID)
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
