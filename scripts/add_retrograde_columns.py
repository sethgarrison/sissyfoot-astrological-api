"""
Add retrograde_interpretation column to planet_sign and planet_house tables.
Run for existing databases created before retrograde support. New DBs get the column from create_all.

Usage: python -m scripts.add_retrograde_columns
"""
import asyncio
import os

from sqlalchemy import text

from database.connection import engine, init_db


async def migrate():
    """Add retrograde_interpretation column if missing."""
    await init_db()
    url = str(engine.url)
    async with engine.begin() as conn:
        if "sqlite" in url:
            for table, col in [
                ("planet_sign_interpretations", "retrograde_interpretation"),
                ("planet_house_interpretations", "retrograde_interpretation"),
            ]:
                try:
                    await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} TEXT'))
                    print(f"Added {col} to {table}")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        print(f"{col} already exists in {table}, skipping")
                    else:
                        raise
        else:
            for table, col in [
                ("planet_sign_interpretations", "retrograde_interpretation"),
                ("planet_house_interpretations", "retrograde_interpretation"),
            ]:
                try:
                    await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} TEXT'))
                    print(f"Added {col} to {table} (or already exists)")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"{col} already exists in {table}, skipping")
                    else:
                        raise
    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
