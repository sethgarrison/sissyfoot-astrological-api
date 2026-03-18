"""
Migration: add Big Three tables, aspect type column, and aspect_type_interpretations.
Run after add_retrograde_columns and add_unique_constraints.
Usage: python -m scripts.add_big_three_and_aspect_type
"""
import asyncio

from sqlalchemy import text

from database.connection import engine, init_db


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
    """Add aspects.type_, Big Three tables, aspect_type_interpretations."""
    await init_db()
    url = str(engine.url)
    async with engine.begin() as conn:
        # Aspects: type_ column (conjunction, stressful, easy-flowing)
        await _add_column_if_missing(conn, "aspects", "type_", "VARCHAR(30)")

        if "sqlite" in url:
            for table_sql, name in [
                ("""
                    CREATE TABLE IF NOT EXISTS sun_sign_interpretations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sign_id INTEGER NOT NULL REFERENCES signs(id),
                        archetypes_balanced VARCHAR(500),
                        archetypes_unbalanced VARCHAR(500),
                        journey VARCHAR(200),
                        gifts TEXT,
                        challenges TEXT,
                        interpretation TEXT
                    )
                """, "sun_sign_interpretations"),
                ("""
                    CREATE TABLE IF NOT EXISTS moon_sign_interpretations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sign_id INTEGER NOT NULL REFERENCES signs(id),
                        nature VARCHAR(500),
                        sources_of_contentment VARCHAR(500),
                        keywords VARCHAR(500),
                        interpretation TEXT
                    )
                """, "moon_sign_interpretations"),
                ("""
                    CREATE TABLE IF NOT EXISTS ascendant_sign_interpretations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sign_id INTEGER NOT NULL REFERENCES signs(id),
                        impression VARCHAR(500),
                        appearance VARCHAR(500),
                        childhood VARCHAR(500),
                        balance VARCHAR(500),
                        interpretation TEXT
                    )
                """, "ascendant_sign_interpretations"),
                ("""
                    CREATE TABLE IF NOT EXISTS aspect_type_interpretations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type_key VARCHAR(30) NOT NULL UNIQUE,
                        interpretation_text TEXT NOT NULL
                    )
                """, "aspect_type_interpretations"),
            ]:
                try:
                    await conn.execute(text(table_sql))
                    print(f"Created {name} table (or already exists)")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        raise

    print("Big Three and aspect type migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
