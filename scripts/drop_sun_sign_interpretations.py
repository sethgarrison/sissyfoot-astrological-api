"""
Drop sun_sign_interpretations table (Sun data merged into signs).
Run after scripts.merge_sun_into_signs.

Usage: python -m scripts.drop_sun_sign_interpretations
"""
import asyncio
from sqlalchemy import text

from database.connection import init_db, engine


async def main():
    await init_db()
    async with engine.begin() as conn:
        dialect = engine.url.get_dialect().name
        if dialect == "sqlite":
            await conn.execute(text("DROP TABLE IF EXISTS sun_sign_interpretations"))
        else:
            await conn.execute(text("DROP TABLE IF EXISTS sun_sign_interpretations"))
    print("Dropped sun_sign_interpretations table.")


if __name__ == "__main__":
    asyncio.run(main())
