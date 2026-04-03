"""
Migration: add new columns and tables for expanded interpretation data.
Run for existing databases. New DBs get everything from create_all.

Usage: python -m scripts.add_retrograde_columns
"""
import asyncio

from sqlalchemy import text

from core.db.base import Base
from core.db.connection import engine, init_db


async def _add_column_if_missing(conn, table: str, col: str, col_type: str = "TEXT"):
    """Add column to table if it doesn't exist."""
    url = str(engine.url)
    try:
        if "sqlite" in url:
            await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
        else:
            await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}'))
        print(f"Added {col} to {table}")
        return True
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print(f"{col} already exists in {table}, skipping")
            return False
        raise


async def migrate():
    """Add new columns and tables if missing."""
    await init_db()
    url = str(engine.url)
    async with engine.begin() as conn:
        # Retrograde columns
        for table, col in [
            ("planet_sign_interpretations", "retrograde_interpretation"),
            ("planet_house_interpretations", "retrograde_interpretation"),
        ]:
            await _add_column_if_missing(conn, table, col)

        # Planets: description, keywords
        for col in ["description", "keywords"]:
            await _add_column_if_missing(conn, "planets", col)

        # Signs: archetypes_balanced, archetypes_unbalanced, journey, gifts, challenges, interpretation
        for col in ["archetypes_balanced", "archetypes_unbalanced", "journey", "gifts", "challenges", "interpretation"]:
            await _add_column_if_missing(conn, "signs", col)

        # Houses: description, subtitle, keywords
        for col in ["description", "subtitle", "keywords"]:
            await _add_column_if_missing(conn, "houses", col)

        # Planet-sign: interpretation_long, interpretation_short, keywords
        for col in ["interpretation_long", "interpretation_short", "keywords"]:
            await _add_column_if_missing(conn, "planet_sign_interpretations", col)

        # Planet-house: short_interpretation
        await _add_column_if_missing(conn, "planet_house_interpretations", "short_interpretation")

        # Create sign_house_interpretations table if missing (SQLite: check by creating)
        if "sqlite" in url:
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sign_house_interpretations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        house_id INTEGER NOT NULL REFERENCES houses(id),
                        sign_id INTEGER NOT NULL REFERENCES signs(id),
                        interpretation_text TEXT NOT NULL
                    )
                """))
                print("Created sign_house_interpretations table (or already exists)")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    raise

        # Create planet_aspect_interpretations table if missing
        if "sqlite" in url:
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS planet_aspect_interpretations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        planet_1_id INTEGER NOT NULL REFERENCES planets(id),
                        planet_2_id INTEGER NOT NULL REFERENCES planets(id),
                        aspect_id INTEGER NOT NULL REFERENCES aspects(id),
                        interpretation_text TEXT NOT NULL
                    )
                """))
                print("Created planet_aspect_interpretations table (or already exists)")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    raise

    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
