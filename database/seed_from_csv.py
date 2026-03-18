"""
Seed database from CSVs in data/new/. Run after init_db.
Loads and updates interpretations from your filled-in data.

By default, preserves existing non-placeholder content (won't overwrite real data
with empty/placeholder values from CSV). Use --overwrite to force updates.

Usage: python -m database.seed_from_csv [--overwrite]
"""
import argparse
import asyncio
import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interpretations.data_quality import is_placeholder_text

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
    SunSignInterpretation,
    MoonSignInterpretation,
    AscendantSignInterpretation,
    AspectTypeInterpretation,
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


def _is_real_content(val) -> bool:
    """True if value has meaningful non-placeholder content."""
    if val is None or (isinstance(val, str) and not val.strip()):
        return False
    return not is_placeholder_text(str(val))


def _should_update_field(existing_val, new_val: str | None, overwrite: bool) -> bool:
    """When overwrite=False, preserve existing real content from empty/placeholder CSV values."""
    if overwrite:
        return True
    if not new_val or (isinstance(new_val, str) and not new_val.strip()):
        return False  # Never overwrite with empty
    if is_placeholder_text(str(new_val)):
        return not _is_real_content(existing_val)  # Don't overwrite real with placeholder
    return True  # New is real content, always update


async def load_from_csv(session: AsyncSession, *, overwrite: bool = False) -> None:
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

    # 3b. Update Aspects from aspects.csv (type column: conjunction, stressful, easy-flowing)
    for row in _read_csv(_csv_path("aspects.csv")):
        name = (row.get("name") or "").strip()
        type_val = (row.get("type") or "").strip()
        if not name:
            continue
        a = aspect_by_name.get(name.lower())
        if a and type_val:
            a.type_ = type_val
            session.add(a)

    # 3c. Sun sign interpretations (Big Three) from sun.csv
    for row in _read_csv(_csv_path("sun.csv")):
        name = (row.get("Signs") or row.get("signs") or row.get("name") or "").strip()
        if not name:
            continue
        sid = sign_by_name.get(name.lower())
        if not sid:
            continue
        existing = (
            await session.execute(
                select(SunSignInterpretation).where(
                    SunSignInterpretation.sign_id == sid.id,
                )
            )
        ).scalar_one_or_none()
        data = {
            "archetypes_balanced": (row.get("archetypes_balanced") or "").strip() or None,
            "archetypes_unbalanced": (row.get("archetypes_unbalanced") or "").strip() or None,
            "journey": (row.get("journey") or "").strip() or None,
            "gifts": (row.get("gifts") or "").strip() or None,
            "challenges": (row.get("challenges") or "").strip() or None,
            "interpretation": (row.get("interpretation") or "").strip() or None,
        }
        if existing:
            for k, v in data.items():
                if v is not None and _should_update_field(getattr(existing, k, None), v, overwrite):
                    setattr(existing, k, v)
            session.add(existing)
        else:
            session.add(SunSignInterpretation(sign_id=sid.id, **data))

    # 3d. Moon sign interpretations (Big Three) from moon.csv
    for row in _read_csv(_csv_path("moon.csv")):
        name = (row.get("signs") or row.get("Signs") or row.get("name") or "").strip()
        if not name:
            continue
        sid = sign_by_name.get(name.lower())
        if not sid:
            continue
        existing = (
            await session.execute(
                select(MoonSignInterpretation).where(
                    MoonSignInterpretation.sign_id == sid.id,
                )
            )
        ).scalar_one_or_none()
        keywords = (row.get("keywords") or row.get("kewords") or "").strip() or None
        data = {
            "nature": (row.get("nature") or "").strip() or None,
            "sources_of_contentment": (row.get("sources_of_contentment") or "").strip() or None,
            "keywords": keywords,
            "interpretation": (row.get("interpretation") or "").strip() or None,
        }
        if existing:
            for k, v in data.items():
                if v is not None and _should_update_field(getattr(existing, k, None), v, overwrite):
                    setattr(existing, k, v)
            session.add(existing)
        else:
            session.add(MoonSignInterpretation(sign_id=sid.id, **data))

    # 3e. Ascendant sign interpretations (Big Three) from ascendent.csv
    for row in _read_csv(_csv_path("ascendent.csv")):
        name = (row.get("sign") or row.get("Sign") or row.get("name") or "").strip()
        if not name:
            continue
        sid = sign_by_name.get(name.lower())
        if not sid:
            continue
        existing = (
            await session.execute(
                select(AscendantSignInterpretation).where(
                    AscendantSignInterpretation.sign_id == sid.id,
                )
            )
        ).scalar_one_or_none()
        data = {
            "impression": (row.get("impression") or "").strip() or None,
            "appearance": (row.get("appearance") or "").strip() or None,
            "childhood": (row.get("childhood") or "").strip() or None,
            "balance": (row.get("balance") or "").strip() or None,
            "interpretation": (row.get("interpretation") or "").strip() or None,
        }
        if existing:
            for k, v in data.items():
                if v is not None and _should_update_field(getattr(existing, k, None), v, overwrite):
                    setattr(existing, k, v)
            session.add(existing)
        else:
            session.add(AscendantSignInterpretation(sign_id=sid.id, **data))

    # 3f. Aspect type interpretations (conjunction, stressful, easy-flowing)
    for type_key in ("conjunction", "stressful", "easy-flowing"):
        existing = (
            await session.execute(
                select(AspectTypeInterpretation).where(
                    AspectTypeInterpretation.type_key == type_key,
                )
            )
        ).scalar_one_or_none()
        if not existing:
            label = type_key.replace("-", " ").replace("_", " ").title()
            session.add(
                AspectTypeInterpretation(
                    type_key=type_key,
                    interpretation_text=f"[Add interpretation for {label} aspects]",
                )
            )

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
    parser = argparse.ArgumentParser(description="Seed DB from CSV (preserves existing real data by default)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite all fields; default preserves non-placeholder content")
    args = parser.parse_args()
    await init_db()
    async with AsyncSessionLocal() as session:
        # Ensure reference data exists (run database.seed first if needed)
        planets = (await session.execute(select(Planet))).scalars().all()
        if not planets:
            print("Reference data missing. Run 'python -m database.seed' first.")
            return
        await load_from_csv(session, overwrite=args.overwrite)


if __name__ == "__main__":
    asyncio.run(main())
