"""
Add signs.adverb and aspects.summary_keyphrase for editable interpretations_summary lexicon.

Usage: python -m scripts.add_summary_lexicon_columns
"""
import asyncio

from sqlalchemy import text

from core.db.connection import engine, init_db


async def _add_column_if_missing(conn, table: str, col: str, col_type: str = "TEXT"):
    url = str(engine.url)
    try:
        if "sqlite" in url:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
        else:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}"))
        print(f"Added {col} to {table}")
        return True
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print(f"{col} already exists in {table}, skipping")
            return False
        raise


async def migrate():
    await init_db()
    async with engine.begin() as conn:
        await _add_column_if_missing(conn, "signs", "adverb", "VARCHAR(100)")
        await _add_column_if_missing(conn, "aspects", "summary_keyphrase", "VARCHAR(255)")


if __name__ == "__main__":
    asyncio.run(migrate())
