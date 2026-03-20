"""
Merge sun_sign_interpretations into signs table.
Copies archetypes_balanced, archetypes_unbalanced, journey, gifts, challenges, interpretation
from sun_sign_interpretations into the corresponding sign row.

Run after database.seed and database.seed_from_csv. Run before dropping sun_sign_interpretations.
Uses raw SQL so it works even after SunSignInterpretation model is removed.

Usage: python -m scripts.merge_sun_into_signs
"""
import asyncio
from sqlalchemy import text

from database.connection import init_db, engine


async def _expand_sign_columns_if_needed():
    """Expand Sign columns to fit sun data (e.g. VARCHAR(200) -> VARCHAR(500))."""
    # PostgreSQL: ALTER COLUMN; SQLite: no-op (VARCHAR is flexible)
    dialect = engine.url.get_dialect().name
    if dialect == "postgresql":
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE signs ALTER COLUMN archetypes_balanced TYPE VARCHAR(500)"))
            await conn.execute(text("ALTER TABLE signs ALTER COLUMN archetypes_unbalanced TYPE VARCHAR(500)"))
            await conn.execute(text("ALTER TABLE signs ALTER COLUMN journey TYPE VARCHAR(200)"))
    # SQLite: no alter needed


async def merge_sun_into_signs() -> int:
    """Copy sun_sign_interpretations data into signs via raw SQL. Returns number of signs updated."""
    async with engine.begin() as conn:
        # Check if sun_sign_interpretations exists
        dialect = engine.url.get_dialect().name
        if dialect == "sqlite":
            r = (await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sun_sign_interpretations'"
            ))).scalar()
            if not r:
                return 0
        else:
            r = (await conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sun_sign_interpretations')"
            ))).scalar()
            if not r:
                return 0

        if dialect == "postgresql":
            await conn.execute(text("""
                UPDATE signs s SET
                    archetypes_balanced = COALESCE(ss.archetypes_balanced, s.archetypes_balanced),
                    archetypes_unbalanced = COALESCE(ss.archetypes_unbalanced, s.archetypes_unbalanced),
                    journey = COALESCE(ss.journey, s.journey),
                    gifts = COALESCE(ss.gifts, s.gifts),
                    challenges = COALESCE(ss.challenges, s.challenges),
                    interpretation = COALESCE(ss.interpretation, s.interpretation)
                FROM sun_sign_interpretations ss
                WHERE ss.sign_id = s.id
            """))
        else:
            # SQLite: update each sign from sun row
            rows = (await conn.execute(text(
                "SELECT sign_id, archetypes_balanced, archetypes_unbalanced, journey, gifts, challenges, interpretation FROM sun_sign_interpretations"
            ))).fetchall()
            for row in rows:
                await conn.execute(text("""
                    UPDATE signs SET
                        archetypes_balanced = COALESCE(:ab, archetypes_balanced),
                        archetypes_unbalanced = COALESCE(:au, archetypes_unbalanced),
                        journey = COALESCE(:j, journey),
                        gifts = COALESCE(:g, gifts),
                        challenges = COALESCE(:c, challenges),
                        interpretation = COALESCE(:i, interpretation)
                    WHERE id = :sid
                """), {"sid": row[0], "ab": row[1], "au": row[2], "j": row[3], "g": row[4], "c": row[5], "i": row[6]})

        result = (await conn.execute(text("SELECT COUNT(*) FROM sun_sign_interpretations"))).scalar()
        count = int(result) if result is not None else 0
    return count


async def main():
    await init_db()
    try:
        await _expand_sign_columns_if_needed()
    except Exception as e:
        print(f"Note: column expansion skipped ({e})")
    try:
        count = await merge_sun_into_signs()
        print(f"Merged sun data into {count} signs.")
    except Exception as e:
        print(f"Merge failed (table may already be dropped): {e}")


if __name__ == "__main__":
    asyncio.run(main())
