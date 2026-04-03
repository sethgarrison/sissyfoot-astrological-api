"""
Delete all saved chart readings (readings table only — interpretation tables untouched).

Usage (from repo root):
  python -m scripts.clear_readings

Uses DATABASE_URL if set; otherwise local SQLite ./natal_chart.db.
"""
import asyncio

from sqlalchemy import delete

from astrology.db.models import Reading
from core.db.connection import engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.execute(delete(Reading))
        print("Cleared readings table (all saved charts removed).")


if __name__ == "__main__":
    asyncio.run(main())
