"""
Seed placeholder interpretation data. Run once after DB creation.
Usage: python -m database.seed
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import engine, AsyncSessionLocal, init_db
from .models import (
    Planet,
    Sign,
    House,
    Aspect,
    PlanetSignInterpretation,
    PlanetHouseInterpretation,
    AspectInterpretation,
    ChartShapeInterpretation,
    ChartDistributionInterpretation,
    ModalityElementDistributionInterpretation,
)

PLACEHOLDER = "[Add your interpretation here]"

PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron",
]

SIGNS = [
    ("Aries", "fire", "cardinal"),
    ("Taurus", "earth", "fixed"),
    ("Gemini", "air", "mutable"),
    ("Cancer", "water", "cardinal"),
    ("Leo", "fire", "fixed"),
    ("Virgo", "earth", "mutable"),
    ("Libra", "air", "cardinal"),
    ("Scorpio", "water", "fixed"),
    ("Sagittarius", "fire", "mutable"),
    ("Capricorn", "earth", "cardinal"),
    ("Aquarius", "air", "fixed"),
    ("Pisces", "water", "mutable"),
]

HOUSE_TYPES = {
    1: "angular", 4: "angular", 7: "angular", 10: "angular",
    2: "succedent", 5: "succedent", 8: "succedent", 11: "succedent",
    3: "cadent", 6: "cadent", 9: "cadent", 12: "cadent",
}

ASPECTS = [
    ("Conjunction", 0, "☌"),
    ("Opposition", 180, "☍"),
    ("Square", 90, "□"),
    ("Trine", 120, "△"),
    ("Sextile", 60, "⚹"),
    ("Quincunx", 150, "⚻"),
]

CHART_SHAPES = [
    "splash", "splay", "bundle", "bowl", "locomotive", "bucket", "see_saw",
]

CHART_DISTRIBUTIONS = [
    # Hemisphere emphasis: >50% of planets in that half
    "hemisphere_northern",
    "hemisphere_southern",
    "hemisphere_eastern",
    "hemisphere_western",
    # Quadrant emphasis: >50% of planets in that quarter
    "quadrant_1",
    "quadrant_2",
    "quadrant_3",
    "quadrant_4",
    # Spread: planets distributed across regions, no single majority
    "hemisphere_spread_north_south",  # planets in both N and S, neither >50%
    "hemisphere_spread_east_west",    # planets in both E and W, neither >50%
    "quadrant_spread",                # no quadrant has >50%, planets in 2+ quadrants
]

# Modality/element distribution keys (based on planetary placements in signs)
# See interpretations/modality_element.py for detection logic
MODALITY_ELEMENT_KEYS = [
    "element_fire_dominant",
    "element_earth_dominant",
    "element_air_dominant",
    "element_water_dominant",
    "element_balanced",
    "element_lacking_fire",
    "element_lacking_earth",
    "element_lacking_air",
    "element_lacking_water",
    "quality_cardinal_dominant",
    "quality_fixed_dominant",
    "quality_mutable_dominant",
    "quality_balanced",
]


async def seed(session: AsyncSession):

    # Planets
    for name in PLANETS:
        r = await session.execute(select(Planet).where(Planet.name == name))
        if r.scalar_one_or_none() is None:
            session.add(Planet(name=name))

    # Signs
    for name, element, modality in SIGNS:
        r = await session.execute(select(Sign).where(Sign.name == name))
        if r.scalar_one_or_none() is None:
            session.add(Sign(name=name, element=element, modality=modality))

    # Houses
    for num in range(1, 13):
        r = await session.execute(select(House).where(House.number == num))
        if r.scalar_one_or_none() is None:
            session.add(House(number=num, type_=HOUSE_TYPES.get(num)))

    # Aspects
    for name, angle, symbol in ASPECTS:
        r = await session.execute(select(Aspect).where(Aspect.name == name))
        if r.scalar_one_or_none() is None:
            session.add(Aspect(name=name, angle_degrees=angle, symbol=symbol))

    await session.commit()

    # Fetch IDs
    planet_rows = (await session.execute(select(Planet))).scalars().all()
    sign_rows = (await session.execute(select(Sign))).scalars().all()
    house_rows = (await session.execute(select(House))).scalars().all()
    aspect_rows = (await session.execute(select(Aspect))).scalars().all()

    planet_by_name = {p.name: p.id for p in planet_rows}
    sign_by_name = {s.name: s.id for s in sign_rows}
    house_by_num = {h.number: h.id for h in house_rows}
    aspect_by_name = {a.name: a.id for a in aspect_rows}

    # Planet-Sign interpretations
    for pname in PLANETS:
        for sname, _, _ in SIGNS:
            pid, sid = planet_by_name[pname], sign_by_name[sname]
            r = await session.execute(
                select(PlanetSignInterpretation).where(
                    PlanetSignInterpretation.planet_id == pid,
                    PlanetSignInterpretation.sign_id == sid,
                )
            )
            if r.scalar_one_or_none() is None:
                session.add(PlanetSignInterpretation(
                    planet_id=pid, sign_id=sid,
                    interpretation_text=f"{pname} in {sname}: {PLACEHOLDER}",
                ))

    # Planet-House interpretations
    for pname in PLANETS:
        for num in range(1, 13):
            pid, hid = planet_by_name[pname], house_by_num[num]
            r = await session.execute(
                select(PlanetHouseInterpretation).where(
                    PlanetHouseInterpretation.planet_id == pid,
                    PlanetHouseInterpretation.house_id == hid,
                )
            )
            if r.scalar_one_or_none() is None:
                session.add(PlanetHouseInterpretation(
                    planet_id=pid, house_id=hid,
                    interpretation_text=f"{pname} in House {num}: {PLACEHOLDER}",
                ))

    # Aspect interpretations (generic)
    for name, _, _ in ASPECTS:
        aid = aspect_by_name[name]
        r = await session.execute(
            select(AspectInterpretation).where(AspectInterpretation.aspect_id == aid)
        )
        if r.scalar_one_or_none() is None:
            session.add(AspectInterpretation(
                aspect_id=aid,
                interpretation_text=f"{name} aspect: {PLACEHOLDER}",
            ))

    # Chart shape interpretations
    for key in CHART_SHAPES:
        r = await session.execute(
            select(ChartShapeInterpretation).where(ChartShapeInterpretation.shape_key == key)
        )
        if r.scalar_one_or_none() is None:
            label = key.replace("_", " ").title()
            session.add(ChartShapeInterpretation(
                shape_key=key,
                interpretation_text=f"The {label} pattern: {PLACEHOLDER}",
            ))

    # Chart distribution interpretations
    for key in CHART_DISTRIBUTIONS:
        r = await session.execute(
            select(ChartDistributionInterpretation).where(
                ChartDistributionInterpretation.distribution_key == key
            )
        )
        if r.scalar_one_or_none() is None:
            label = key.replace("_", " ").replace(" 1", " 1st").replace(" 2", " 2nd").replace(" 3", " 3rd").replace(" 4", " 4th").title()
            if "spread" in key:
                session.add(ChartDistributionInterpretation(
                    distribution_key=key,
                    interpretation_text=f"{label} (planets distributed across regions): {PLACEHOLDER}",
                ))
            else:
                session.add(ChartDistributionInterpretation(
                    distribution_key=key,
                    interpretation_text=f"{label} emphasis: {PLACEHOLDER}",
                ))

    # Modality/Element distribution interpretations
    for key in MODALITY_ELEMENT_KEYS:
        r = await session.execute(
            select(ModalityElementDistributionInterpretation).where(
                ModalityElementDistributionInterpretation.distribution_key == key
            )
        )
        if r.scalar_one_or_none() is None:
            if key.startswith("element_"):
                if "dominant" in key:
                    elem = key.split("_")[1]
                    label = f"Fire/Earth/Air/Water emphasis: {elem.title()} dominant"
                elif "lacking" in key:
                    elem = key.split("_")[-1]
                    label = f"Missing element: no planets in {elem.title()}"
                else:
                    label = "Element balance: no single element dominant"
            else:
                if "dominant" in key:
                    mod = key.split("_")[1]
                    label = f"Modality emphasis: {mod.title()} dominant"
                else:
                    label = "Modality balance: no single quality dominant"
            session.add(ModalityElementDistributionInterpretation(
                distribution_key=key,
                interpretation_text=f"{label}: {PLACEHOLDER}",
            ))

    await session.commit()
    print("Seed complete.")


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
