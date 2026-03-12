"""Fetch interpretations from the database."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
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


async def fetch_interpretations(
    session: AsyncSession,
    planet_sign_pairs: list[tuple[str, str]],
    planet_house_pairs: list[tuple[str, int]],
    aspect_keys: list[str],
    chart_shape: Optional[str],
    distribution_keys: list[str],
    modality_element_keys: list[str] | None = None,
    retrograde_planets: set[str] | None = None,
) -> dict:
    """
    Fetch all relevant interpretations. Returns a dict matching the API response shape.
    When a planet is retrograde, fetches retrograde_interpretation from planet_sign and planet_house tables.
    """
    result = {
        "planet_in_sign": {},
        "planet_in_house": {},
        "aspects": {},
        "chart_shape": {
            "primary": chart_shape,
            "interpretation": None,
            "distribution": {},
        },
        "modality_element_distribution": {},
        "retrograde_planets": [],
        "retrograde_interpretations": {},
    }

    retrograde_planets = retrograde_planets or set()
    result["retrograde_planets"] = sorted(retrograde_planets)

    empty = (
        not planet_sign_pairs
        and not planet_house_pairs
        and not aspect_keys
        and not chart_shape
        and not distribution_keys
        and not modality_element_keys
        and not retrograde_planets
    )
    if empty:
        return result

    # Build lookup maps
    planet_rows = (await session.execute(select(Planet))).scalars().all()
    sign_rows = (await session.execute(select(Sign))).scalars().all()
    house_rows = (await session.execute(select(House))).scalars().all()
    aspect_rows = (await session.execute(select(Aspect))).scalars().all()

    planet_by_name = {p.name: p.id for p in planet_rows}
    sign_by_name = {s.name: s.id for s in sign_rows}
    house_by_num = {h.number: h.id for h in house_rows}
    aspect_by_name = {a.name: a.id for a in aspect_rows}

    retrograde = retrograde_planets or set()
    if retrograde:
        result["retrograde_planets"] = sorted(retrograde)

    # Planet-Sign
    for pname, sname in planet_sign_pairs:
        pid = planet_by_name.get(pname)
        sid = sign_by_name.get(sname)
        if pid is None or sid is None:
            continue
        key = f"{pname} in {sname}"
        r = await session.execute(
            select(
                PlanetSignInterpretation.interpretation_text,
                PlanetSignInterpretation.retrograde_interpretation,
            ).where(
                PlanetSignInterpretation.planet_id == pid,
                PlanetSignInterpretation.sign_id == sid,
            )
        )
        row = r.one_or_none()
        if row:
            result["planet_in_sign"][key] = row.interpretation_text
            if pname in retrograde and row.retrograde_interpretation:
                result["retrograde_interpretations"][key] = row.retrograde_interpretation

    # Planet-House
    for pname, hnum in planet_house_pairs:
        pid = planet_by_name.get(pname)
        hid = house_by_num.get(hnum)
        if pid is None or hid is None:
            continue
        key = f"{pname} in House {hnum}"
        r = await session.execute(
            select(
                PlanetHouseInterpretation.interpretation_text,
                PlanetHouseInterpretation.retrograde_interpretation,
            ).where(
                PlanetHouseInterpretation.planet_id == pid,
                PlanetHouseInterpretation.house_id == hid,
            )
        )
        row = r.one_or_none()
        if row:
            result["planet_in_house"][key] = row.interpretation_text
            if pname in retrograde and row.retrograde_interpretation:
                result["retrograde_interpretations"][key] = row.retrograde_interpretation

    # Aspects - generic (aspect type only) for now
    for aspect_key in aspect_keys:
        # aspect_key could be "Sun square Moon" - we use the aspect name "Square"
        # For now we only have generic aspect interpretations, so we need to map
        # "Sun square Moon" -> lookup "Square"
        parts = aspect_key.split()
        aspect_name = parts[-1] if len(parts) >= 2 else aspect_key  # "Square", "Trine", etc.
        aid = aspect_by_name.get(aspect_name)
        if aid is None:
            continue
        r = await session.execute(
            select(AspectInterpretation.interpretation_text).where(
                AspectInterpretation.aspect_id == aid
            )
        )
        text = r.scalar_one_or_none()
        if text:
            result["aspects"][aspect_key] = text

    # Chart shape
    if chart_shape:
        r = await session.execute(
            select(ChartShapeInterpretation.interpretation_text).where(
                ChartShapeInterpretation.shape_key == chart_shape
            )
        )
        text = r.scalar_one_or_none()
        if text:
            result["chart_shape"]["interpretation"] = text

    # Chart distributions
    for dkey in distribution_keys:
        r = await session.execute(
            select(ChartDistributionInterpretation.interpretation_text).where(
                ChartDistributionInterpretation.distribution_key == dkey
            )
        )
        text = r.scalar_one_or_none()
        if text:
            result["chart_shape"]["distribution"][dkey] = text

    # Modality/element distribution (from planetary placements by sign)
    for key in modality_element_keys or []:
        r = await session.execute(
            select(ModalityElementDistributionInterpretation.interpretation_text).where(
                ModalityElementDistributionInterpretation.distribution_key == key
            )
        )
        text = r.scalar_one_or_none()
        if text:
            result["modality_element_distribution"][key] = text

    return result
