"""
Migration: deduplicate interpretation tables and add unique constraints.
Run after add_retrograde_columns. Fixes duplicates from manual seeding.

Usage: python -m scripts.add_unique_constraints
"""
import asyncio

from sqlalchemy import text

from core.db.connection import engine, init_db


async def _dedupe_and_index(conn, table: str, key_cols: list[str], index_name: str):
    """Remove duplicate rows (keep min id per key), then create unique index."""
    url = str(engine.url)
    cols = ", ".join(key_cols)
    where_parts = " AND ".join(f"p1.{c} = p2.{c}" for c in key_cols)

    # Delete duplicates: keep row with smallest id for each (planet_id, sign_id) etc
    delete_sql = f"""
        DELETE FROM {table}
        WHERE id IN (
            SELECT p1.id FROM {table} p1
            WHERE EXISTS (
                SELECT 1 FROM {table} p2
                WHERE {where_parts} AND p1.id > p2.id
            )
        )
    """
    try:
        await conn.execute(text(delete_sql))
        print(f"Deduplicated {table}")
    except Exception as e:
        err = str(e).lower()
        if "no such table" in err:
            print(f"Skipping {table} (table does not exist)")
            return
        print(f"Dedupe {table}: {e}")

    # Create unique index if not exists
    create_sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table} ({cols})"
    try:
        await conn.execute(text(create_sql))
        print(f"Created index {index_name} on {table}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"Index {index_name} already exists on {table}")
        else:
            raise


async def migrate():
    """Deduplicate interpretation tables and add unique indexes."""
    await init_db()
    async with engine.begin() as conn:
        await _dedupe_and_index(
            conn,
            "planet_sign_interpretations",
            ["planet_id", "sign_id"],
            "uq_planet_sign_idx",
        )
        await _dedupe_and_index(
            conn,
            "planet_house_interpretations",
            ["planet_id", "house_id"],
            "uq_planet_house_idx",
        )
        await _dedupe_and_index(
            conn,
            "sign_house_interpretations",
            ["house_id", "sign_id"],
            "uq_sign_house_idx",
        )
        await _dedupe_and_index(
            conn,
            "planet_aspect_interpretations",
            ["planet_1_id", "planet_2_id", "aspect_id"],
            "uq_planet_aspect_idx",
        )
        await _dedupe_and_index(
            conn,
            "aspect_interpretations",
            ["aspect_id"],
            "uq_aspect_interpretation_idx",
        )
    print("Unique constraints migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
