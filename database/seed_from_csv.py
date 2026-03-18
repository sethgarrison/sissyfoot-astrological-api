"""
Seed database from CSVs in data/new/. Run after init_db.
Loads and updates interpretations from your filled-in data.
Usage: python -m database.seed_from_csv
"""
import asyncio
import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import AsyncSessionLocal, init_db
from .models import (
    Planet,
    Sign,
    House,
    Aspect,
    PlanetSignInterpretation,
    PlanetHouseInterpretation,
    ChartShapeInterpretation,
    ChartDistributionInterpretation,
    SignHouseInterpretation,
    PlanetAspectInterpretation,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "new"


def _csv_path(name: str) -> Path:
    return DATA_DIR / f"Astro Data - {name}.csv"


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()})
    return rows


async def load_from_csv(session: AsyncSession) -> None:
    """Load interpretation data from data/new/ CSVs."""
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        print("Create data/new/ and add your 'Astro Data - *.csv' files.")
        return

    # Build lookup maps (reference tables must already exist from database.seed)
    planet_rows = (await session.execute(select(Planet))).scalars().all()
    sign_rows = (await session.execute(select(Sign))).scalars().all()
    house_rows = (await session.execute(select(House))).scalars().all()
    aspect_rows = (await session.execute(select(Aspect))).scalars().all()

    planet_by_name = {p.name.lower(): p for p in planet_rows}
    sign_by_name = {s.name.lower(): s for s in sign_rows}
    house_by_num = {h.number: h for h in house_rows}
    aspect_by_name = {a.name.lower(): a for a in aspect_rows}

    # 1. Update Planets from Astro Data - planets.csv
    for row in _read_csv(_csv_path("planets.csv")):
        name = row.get("name", "").strip()
        if not name:
            continue
        p = planet_by_name.get(name.lower())
        if p:
            p.description = row.get("description") or p.description
            p.keywords = row.get("keywords") or p.keywords
            session.add(p)

    # 2. Update Signs from Astro Data - signs.csv (column "Signs" = name)
    for row in _read_csv(_csv_path("signs.csv")):
        name = (row.get("Signs") or row.get("signs") or row.get("name") or "").strip()
        if not name:
            continue
        s = sign_by_name.get(name.lower())
        if s:
            s.archetypes_balanced = row.get("archetypes_balanced") or s.archetypes_balanced
            s.archetypes_unbalanced = row.get("archetypes_unbalanced") or s.archetypes_unbalanced
            s.journey = row.get("journey") or s.journey
            s.gifts = row.get("gifts") or s.gifts
            s.challenges = row.get("challenges") or s.challenges
            s.interpretation = row.get("interpretation") or s.interpretation
            session.add(s)

    # 3. Update Houses from Astro Data - houses.csv
    for row in _read_csv(_csv_path("houses.csv")):
        try:
            num = int(row.get("number", row.get("id", 0)))
        except (ValueError, TypeError):
            continue
        h = house_by_num.get(num)
        if h:
            h.description = row.get("description") or h.description
            h.subtitle = row.get("subtitle") or h.subtitle
            h.keywords = row.get("keywords") or h.keywords
            session.add(h)

    await session.flush()

    # 4. Planet-Sign interpretations
    for row in _read_csv(_csv_path("planet_sign_interpretations.csv")):
        pname = (row.get("planet") or "").strip()
        sname = (row.get("sign") or "").strip()
        if not pname or not sname:
            continue
        pid = planet_by_name.get(pname.lower())
        sid = sign_by_name.get(sname.lower())
        if not pid or not sid:
            continue

        interp_long = row.get("interpretation_long", "").strip()
        interp_short = row.get("interpretation_short", "").strip()
        keywords = row.get("keywords", "").strip()

        existing = (
            await session.execute(
                select(PlanetSignInterpretation).where(
                    PlanetSignInterpretation.planet_id == pid.id,
                    PlanetSignInterpretation.sign_id == sid.id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            if interp_long:
                existing.interpretation_text = interp_long
            if interp_short:
                existing.interpretation_short = interp_short
            if keywords:
                existing.keywords = keywords
            existing.interpretation_long = interp_long or existing.interpretation_long
            session.add(existing)
        else:
            session.add(
                PlanetSignInterpretation(
                    planet_id=pid.id,
                    sign_id=sid.id,
                    interpretation_text=interp_long or "[Add interpretation]",
                    interpretation_long=interp_long or None,
                    interpretation_short=interp_short or None,
                    keywords=keywords or None,
                )
            )

    # 5. Planet-House interpretations
    for row in _read_csv(_csv_path("planet_house_interpretations.csv")):
        pname = (row.get("planet") or "").strip()
        try:
            hnum = int(row.get("house", row.get("number", 0)))
        except (ValueError, TypeError):
            continue
        if not pname:
            continue
        pid = planet_by_name.get(pname.lower())
        hid = house_by_num.get(hnum)
        if not pid or not hid:
            continue

        interp = row.get("interpretation_text", "").strip()
        short_interp = row.get("short_interpretation", "").strip()

        existing = (
            await session.execute(
                select(PlanetHouseInterpretation).where(
                    PlanetHouseInterpretation.planet_id == pid.id,
                    PlanetHouseInterpretation.house_id == hid.id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            if interp:
                existing.interpretation_text = interp
            if short_interp:
                existing.short_interpretation = short_interp
            session.add(existing)
        else:
            session.add(
                PlanetHouseInterpretation(
                    planet_id=pid.id,
                    house_id=hid.id,
                    interpretation_text=interp or "[Add interpretation]",
                    short_interpretation=short_interp or None,
                )
            )

    # 6. Sign-House interpretations (new table)
    for row in _read_csv(_csv_path("sign_house_interpretations.csv")):
        try:
            hnum = int(row.get("house", 0))
        except (ValueError, TypeError):
            continue
        sname = (row.get("sign") or "").strip()
        interp = (row.get("interpretation") or "").strip()
        if not sname or not interp:
            continue
        sid = sign_by_name.get(sname.lower())
        hid = house_by_num.get(hnum)
        if not sid or not hid:
            continue

        existing = (
            await session.execute(
                select(SignHouseInterpretation).where(
                    SignHouseInterpretation.house_id == hid.id,
                    SignHouseInterpretation.sign_id == sid.id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.interpretation_text = interp
            session.add(existing)
        else:
            session.add(
                SignHouseInterpretation(
                    house_id=hid.id,
                    sign_id=sid.id,
                    interpretation_text=interp,
                )
            )

    # 7. Chart shape interpretations
    for row in _read_csv(_csv_path("chart_shape_interpretations.csv")):
        key = (row.get("shape_key") or "").strip()
        interp = (row.get("interpretation_text") or "").strip()
        if not key or not interp:
            continue
        existing = (
            await session.execute(
                select(ChartShapeInterpretation).where(
                    ChartShapeInterpretation.shape_key == key
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.interpretation_text = interp
            session.add(existing)
        else:
            session.add(
                ChartShapeInterpretation(shape_key=key, interpretation_text=interp)
            )

    # 8. Chart distribution interpretations (keyed by distribution_key)
    for row in _read_csv(_csv_path("chart_distribution_interpretations.csv")):
        key = (row.get("distribution_key") or "").strip()
        interp = (row.get("interpretation_text") or "").strip()
        if not key or not interp:
            continue
        existing = (
            await session.execute(
                select(ChartDistributionInterpretation).where(
                    ChartDistributionInterpretation.distribution_key == key
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.interpretation_text = interp
            session.add(existing)
        else:
            session.add(
                ChartDistributionInterpretation(
                    distribution_key=key, interpretation_text=interp
                )
            )

    # 9. Planet-pair aspect interpretations (from aspect_interpretations.csv)
    for row in _read_csv(_csv_path("aspect_interpretations.csv")):
        p1_name = (row.get("planet_1") or "").strip()
        p2_name = (row.get("planet_2") or "").strip()
        aspect_name = (row.get("aspect") or "").strip()
        interp = (row.get("interpretation_text") or "").strip()
        if not p1_name or not p2_name or not aspect_name or not interp:
            continue
        p1 = planet_by_name.get(p1_name.lower())
        p2 = planet_by_name.get(p2_name.lower())
        a = aspect_by_name.get(aspect_name.lower())
        if not p1 or not p2 or not a:
            continue

        existing = (
            await session.execute(
                select(PlanetAspectInterpretation).where(
                    PlanetAspectInterpretation.planet_1_id == p1.id,
                    PlanetAspectInterpretation.planet_2_id == p2.id,
                    PlanetAspectInterpretation.aspect_id == a.id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.interpretation_text = interp
            session.add(existing)
        else:
            session.add(
                PlanetAspectInterpretation(
                    planet_1_id=p1.id,
                    planet_2_id=p2.id,
                    aspect_id=a.id,
                    interpretation_text=interp,
                )
            )

    await session.commit()
    print("Seed from CSV complete.")


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Ensure reference data exists (run database.seed first if needed)
        planets = (await session.execute(select(Planet))).scalars().all()
        if not planets:
            print("Reference data missing. Run 'python -m database.seed' first.")
            return
        await load_from_csv(session)


if __name__ == "__main__":
    asyncio.run(main())
