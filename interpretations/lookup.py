"""Fetch interpretations from the database."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Planet,
    Sign,
    House,
    Aspect,
    SunSignInterpretation,
    MoonSignInterpretation,
    AscendantSignInterpretation,
    AspectTypeInterpretation,
    PlanetSignInterpretation,
    PlanetHouseInterpretation,
    AspectInterpretation,
    PlanetAspectInterpretation,
    SignHouseInterpretation,
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
    rising_sign: Optional[str] = None,
    sun_sign: Optional[str] = None,
    moon_sign: Optional[str] = None,
    house_cusps: list[tuple[int, str]] | None = None,
) -> dict:
    """
    Fetch all relevant interpretations. Returns a dict matching the API response shape.
    When a planet is retrograde, fetches retrograde_interpretation from planet_sign and planet_house tables.
    """
    result = {
        "planet_in_sign": {},
        "planet_in_house": {},
        "aspects": {},
        "aspects_detail": {},  # aspect_key -> {type, interpretation}
        "big_three": {"sun": None, "moon": None, "ascendant": None},
        "house_sign_interpretations": {},  # (house_num, sign) -> interpretation
        "rising_sign_interpretation": None,
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
    sign_by_name_obj = {s.name: s for s in sign_rows}
    house_by_num = {h.number: h.id for h in house_rows}
    aspect_by_name = {a.name: a for a in aspect_rows}  # full object for type_

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

    # Aspects - prefer planet-pair specific (PlanetAspectInterpretation), fall back to generic
    for aspect_key in aspect_keys:
        # aspect_key: "Sun Square Moon" or "Venus Conjunction Mars"
        parts = aspect_key.split()
        if len(parts) >= 3:
            p1_name, aspect_name, p2_name = parts[0], parts[1], " ".join(parts[2:])
        else:
            aspect_name = parts[-1] if parts else aspect_key
            p1_name = p2_name = None
        aspect_obj = aspect_by_name.get(aspect_name)
        if aspect_obj is None:
            continue
        aid = aspect_obj.id
        type_val = aspect_obj.type_ or None
        text = None
        if p1_name and p2_name:
            p1_id = planet_by_name.get(p1_name)
            p2_id = planet_by_name.get(p2_name)
            if p1_id is not None and p2_id is not None:
                for pid1, pid2 in [(p1_id, p2_id), (p2_id, p1_id)]:
                    r = await session.execute(
                        select(PlanetAspectInterpretation.interpretation_text).where(
                            PlanetAspectInterpretation.planet_1_id == pid1,
                            PlanetAspectInterpretation.planet_2_id == pid2,
                            PlanetAspectInterpretation.aspect_id == aid,
                        )
                    )
                    row = r.one_or_none()
                    if row:
                        text = row[0]
                        break
        if text is None and type_val:
            r = await session.execute(
                select(AspectTypeInterpretation.interpretation_text).where(
                    AspectTypeInterpretation.type_key == type_val
                )
            )
            text = r.scalar_one_or_none()
        if text is None:
            r = await session.execute(
                select(AspectInterpretation.interpretation_text).where(
                    AspectInterpretation.aspect_id == aid
                )
            )
            text = r.scalar_one_or_none()
        if text:
            result["aspects"][aspect_key] = text
        result["aspects_detail"][aspect_key] = {"type": type_val, "interpretation": text}

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

    # Rising sign (SignHouseInterpretation: house 1 + rising sign)
    if rising_sign:
        sid = sign_by_name.get(rising_sign)
        hid = house_by_num.get(1)
        if sid and hid:
            r = await session.execute(
                select(SignHouseInterpretation.interpretation_text).where(
                    SignHouseInterpretation.house_id == hid,
                    SignHouseInterpretation.sign_id == sid,
                )
            )
            row = r.one_or_none()
            if row:
                result["rising_sign_interpretation"] = row.interpretation_text

    # Sign on each house cusp (SignHouseInterpretation)
    for house_num, sign_name in (house_cusps or []):
        sid = sign_by_name.get(sign_name)
        hid = house_by_num.get(house_num)
        if sid and hid:
            r = await session.execute(
                select(SignHouseInterpretation.interpretation_text).where(
                    SignHouseInterpretation.house_id == hid,
                    SignHouseInterpretation.sign_id == sid,
                )
            )
            row = r.one_or_none()
            if row:
                result["house_sign_interpretations"][(house_num, sign_name)] = row.interpretation_text

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

    # Big Three: sun, moon, ascendant from dedicated tables
    if sun_sign:
        sid = sign_by_name.get(sun_sign)
        if sid:
            r = await session.execute(
                select(SunSignInterpretation).where(
                    SunSignInterpretation.sign_id == sid
                )
            )
            sun_row = r.scalar_one_or_none()
            if sun_row:
                sign_obj = sign_by_name_obj.get(sun_sign)
                result["big_three"]["sun"] = {
                    "sign": sun_sign,
                    "archetypes_balanced": sun_row.archetypes_balanced,
                    "archetypes_unbalanced": sun_row.archetypes_unbalanced,
                    "journey": sun_row.journey,
                    "gifts": sun_row.gifts,
                    "challenges": sun_row.challenges,
                    "interpretation": sun_row.interpretation,
                    "sign_interpretation": sign_obj.interpretation if sign_obj else None,
                }
    if moon_sign:
        sid = sign_by_name.get(moon_sign)
        if sid:
            r = await session.execute(
                select(MoonSignInterpretation).where(
                    MoonSignInterpretation.sign_id == sid
                )
            )
            moon_row = r.scalar_one_or_none()
            if moon_row:
                result["big_three"]["moon"] = {
                    "sign": moon_sign,
                    "nature": moon_row.nature,
                    "sources_of_contentment": moon_row.sources_of_contentment,
                    "keywords": moon_row.keywords,
                    "interpretation": moon_row.interpretation,
                }
    if rising_sign:
        sid = sign_by_name.get(rising_sign)
        if sid:
            r = await session.execute(
                select(AscendantSignInterpretation).where(
                    AscendantSignInterpretation.sign_id == sid
                )
            )
            asc_row = r.scalar_one_or_none()
            if asc_row:
                result["big_three"]["ascendant"] = {
                    "sign": rising_sign,
                    "impression": asc_row.impression,
                    "appearance": asc_row.appearance,
                    "childhood": asc_row.childhood,
                    "balance": asc_row.balance,
                    "interpretation": asc_row.interpretation,
                }

    return result
