"""
Data endpoints: expose raw table data for debugging and future interpretation features.
Big Three (sun, moon, ascendant) are the single source of truth for Sun/Moon/Rising interpretations.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import (
    Planet,
    Sign,
    House,
    Aspect,
    SunSignInterpretation,
    MoonSignInterpretation,
    AscendantSignInterpretation,
    PlanetSignInterpretation,
    PlanetHouseInterpretation,
    AspectTypeInterpretation,
    AspectInterpretation,
    PlanetAspectInterpretation,
    SignHouseInterpretation,
    ChartShapeInterpretation,
    ChartDistributionInterpretation,
    ModalityElementDistributionInterpretation,
)


router = APIRouter(prefix="/data", tags=["data"])


# --- Reference tables ---

@router.get("/planets")
async def get_planets(session: AsyncSession = Depends(get_db)):
    """All planets (Sun, Moon, Mercury, etc.)."""
    rows = (await session.execute(select(Planet))).scalars().all()
    return [{"id": r.id, "name": r.name, "symbol": r.symbol, "description": r.description, "keywords": r.keywords} for r in rows]


@router.get("/signs")
async def get_signs(session: AsyncSession = Depends(get_db)):
    """All zodiac signs."""
    rows = (await session.execute(select(Sign))).scalars().all()
    return [{"id": r.id, "name": r.name, "element": r.element, "modality": r.modality, "interpretation": r.interpretation} for r in rows]


@router.get("/houses")
async def get_houses(session: AsyncSession = Depends(get_db)):
    """All houses (1-12)."""
    rows = (await session.execute(select(House))).scalars().all()
    return [{"id": r.id, "number": r.number, "type": r.type_, "description": r.description} for r in rows]


@router.get("/aspects")
async def get_aspects(session: AsyncSession = Depends(get_db)):
    """All aspect types (Conjunction, Opposition, etc.)."""
    rows = (await session.execute(select(Aspect))).scalars().all()
    return [{"id": r.id, "name": r.name, "angle_degrees": r.angle_degrees, "symbol": r.symbol, "type": r.type_} for r in rows]


# --- Big Three: single source of truth for Sun/Moon/Rising interpretations ---

@router.get("/sun")
async def get_sun_interpretations(session: AsyncSession = Depends(get_db)):
    """Sun in sign interpretations (Big Three). One row per sign. Source: sun.csv."""
    rows = (
        await session.execute(
            select(SunSignInterpretation, Sign.name.label("sign_name"))
            .join(Sign, SunSignInterpretation.sign_id == Sign.id)
            .order_by(Sign.id)
        )
    ).fetchall()
    return [
        {
            "id": (s := r[0]).id,
            "sign": r[1],
            "sign_id": s.sign_id,
            "archetypes_balanced": s.archetypes_balanced,
            "archetypes_unbalanced": s.archetypes_unbalanced,
            "journey": s.journey,
            "gifts": s.gifts,
            "challenges": s.challenges,
            "interpretation": s.interpretation,
        }
        for r in rows
    ]


@router.get("/moon")
async def get_moon_interpretations(session: AsyncSession = Depends(get_db)):
    """Moon in sign interpretations (Big Three). One row per sign. Source: moon.csv."""
    rows = (
        await session.execute(
            select(MoonSignInterpretation, Sign.name.label("sign_name"))
            .join(Sign, MoonSignInterpretation.sign_id == Sign.id)
            .order_by(Sign.id)
        )
    ).fetchall()
    return [
        {
            "id": (m := r[0]).id,
            "sign": r[1],
            "sign_id": m.sign_id,
            "nature": m.nature,
            "sources_of_contentment": m.sources_of_contentment,
            "keywords": m.keywords,
            "interpretation": m.interpretation,
        }
        for r in rows
    ]


@router.get("/ascendant")
async def get_ascendant_interpretations(session: AsyncSession = Depends(get_db)):
    """Ascendant/Rising in sign interpretations (Big Three). One row per sign. Source: ascendent.csv."""
    rows = (
        await session.execute(
            select(AscendantSignInterpretation, Sign.name.label("sign_name"))
            .join(Sign, AscendantSignInterpretation.sign_id == Sign.id)
            .order_by(Sign.id)
        )
    ).fetchall()
    return [
        {
            "id": (a := r[0]).id,
            "sign": r[1],
            "sign_id": a.sign_id,
            "impression": a.impression,
            "appearance": a.appearance,
            "childhood": a.childhood,
            "balance": a.balance,
            "interpretation": a.interpretation,
        }
        for r in rows
    ]


# --- Interpretation tables ---

@router.get("/planet-sign")
async def get_planet_sign_interpretations(session: AsyncSession = Depends(get_db)):
    """Planet in sign interpretations (e.g. Sun in Aries)."""
    rows = (
        await session.execute(
            select(
                PlanetSignInterpretation,
                Planet.name.label("planet_name"),
                Sign.name.label("sign_name"),
            )
            .join(Planet, PlanetSignInterpretation.planet_id == Planet.id)
            .join(Sign, PlanetSignInterpretation.sign_id == Sign.id)
            .order_by(Planet.name, Sign.name)
        )
    ).fetchall()
    return [
        {
            "id": (p := r[0]).id,
            "planet": r[1],
            "sign": r[2],
            "interpretation_text": p.interpretation_text,
            "interpretation_long": p.interpretation_long,
            "interpretation_short": p.interpretation_short,
            "keywords": p.keywords,
            "retrograde_interpretation": p.retrograde_interpretation,
        }
        for r in rows
    ]


@router.get("/planet-house")
async def get_planet_house_interpretations(session: AsyncSession = Depends(get_db)):
    """Planet in house interpretations (e.g. Sun in House 1)."""
    rows = (
        await session.execute(
            select(
                PlanetHouseInterpretation,
                Planet.name.label("planet_name"),
                House.number.label("house_number"),
            )
            .join(Planet, PlanetHouseInterpretation.planet_id == Planet.id)
            .join(House, PlanetHouseInterpretation.house_id == House.id)
            .order_by(Planet.name, House.number)
        )
    ).fetchall()
    return [
        {
            "id": (p := r[0]).id,
            "planet": r[1],
            "house": r[2],
            "interpretation_text": p.interpretation_text,
            "short_interpretation": p.short_interpretation,
            "retrograde_interpretation": p.retrograde_interpretation,
        }
        for r in rows
    ]


@router.get("/aspect-type")
async def get_aspect_type_interpretations(session: AsyncSession = Depends(get_db)):
    """Interpretations by aspect type (conjunction, stressful, easy-flowing)."""
    rows = (await session.execute(select(AspectTypeInterpretation))).scalars().all()
    return [{"id": r.id, "type_key": r.type_key, "interpretation_text": r.interpretation_text} for r in rows]


@router.get("/aspect-generic")
async def get_aspect_interpretations(session: AsyncSession = Depends(get_db)):
    """Generic aspect interpretations (one per aspect name, e.g. Conjunction)."""
    rows = (
        await session.execute(
            select(AspectInterpretation, Aspect.name.label("aspect_name"))
            .join(Aspect, AspectInterpretation.aspect_id == Aspect.id)
            .order_by(Aspect.name)
        )
    ).fetchall()
    return [
        {
            "id": (a := r[0]).id,
            "aspect": r[1],
            "interpretation_text": a.interpretation_text,
        }
        for r in rows
    ]


@router.get("/planet-aspect")
async def get_planet_aspect_interpretations(session: AsyncSession = Depends(get_db)):
    """Planet-pair specific aspect interpretations (e.g. Sun conjunct Moon)."""
    from sqlalchemy.orm import aliased
    P1 = aliased(Planet)
    P2 = aliased(Planet)
    rows = (
        await session.execute(
            select(
                PlanetAspectInterpretation,
                P1.name.label("planet_1"),
                P2.name.label("planet_2"),
                Aspect.name.label("aspect_name"),
            )
            .join(P1, PlanetAspectInterpretation.planet_1_id == P1.id)
            .join(P2, PlanetAspectInterpretation.planet_2_id == P2.id)
            .join(Aspect, PlanetAspectInterpretation.aspect_id == Aspect.id)
            .order_by(P1.name, P2.name, Aspect.name)
        )
    ).fetchall()
    return [
        {
            "id": (pa := r[0]).id,
            "planet_1": r[1],
            "planet_2": r[2],
            "aspect": r[3],
            "interpretation_text": pa.interpretation_text,
        }
        for r in rows
    ]


@router.get("/sign-house")
async def get_sign_house_interpretations(session: AsyncSession = Depends(get_db)):
    """Sign on house cusp interpretations (e.g. Aries on House 1 = Aries Rising)."""
    rows = (
        await session.execute(
            select(
                SignHouseInterpretation,
                House.number.label("house_number"),
                Sign.name.label("sign_name"),
            )
            .join(House, SignHouseInterpretation.house_id == House.id)
            .join(Sign, SignHouseInterpretation.sign_id == Sign.id)
            .order_by(House.number, Sign.name)
        )
    ).fetchall()
    return [
        {
            "id": (sh := r[0]).id,
            "house": r[1],
            "sign": r[2],
            "interpretation_text": sh.interpretation_text,
        }
        for r in rows
    ]


@router.get("/chart-shape")
async def get_chart_shape_interpretations(session: AsyncSession = Depends(get_db)):
    """Chart shape interpretations (splash, bundle, bowl, etc.)."""
    rows = (await session.execute(select(ChartShapeInterpretation))).scalars().all()
    return [{"id": r.id, "shape_key": r.shape_key, "interpretation_text": r.interpretation_text} for r in rows]


@router.get("/chart-distribution")
async def get_chart_distribution_interpretations(session: AsyncSession = Depends(get_db)):
    """Hemisphere/quadrant distribution interpretations."""
    rows = (await session.execute(select(ChartDistributionInterpretation))).scalars().all()
    return [{"id": r.id, "distribution_key": r.distribution_key, "interpretation_text": r.interpretation_text} for r in rows]


@router.get("/modality-element")
async def get_modality_element_interpretations(session: AsyncSession = Depends(get_db)):
    """Modality and element distribution interpretations."""
    rows = (await session.execute(select(ModalityElementDistributionInterpretation))).scalars().all()
    return [{"id": r.id, "distribution_key": r.distribution_key, "interpretation_text": r.interpretation_text} for r in rows]
