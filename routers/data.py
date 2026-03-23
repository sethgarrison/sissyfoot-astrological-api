"""
Data endpoints: expose raw table data for debugging and future interpretation features.
Big Three (sun, moon, ascendant) are the single source of truth for Sun/Moon/Rising interpretations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import (
    Planet,
    Sign,
    House,
    Aspect,
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
from schemas.data import (
    PlanetUpdate,
    SignUpdate,
    HouseUpdate,
    AspectUpdate,
    MoonSignInterpretationUpdate,
    AscendantSignInterpretationUpdate,
    PlanetSignInterpretationUpdate,
    PlanetHouseInterpretationUpdate,
    AspectTypeInterpretationUpdate,
    AspectInterpretationUpdate,
    PlanetAspectInterpretationUpdate,
    SignHouseInterpretationUpdate,
    ChartShapeInterpretationUpdate,
    ChartDistributionInterpretationUpdate,
    ModalityElementDistributionInterpretationUpdate,
)


router = APIRouter(prefix="/data", tags=["data"])


def _apply_update(obj, schema_instance):
    """Apply non-None fields from schema to model instance."""
    data = schema_instance.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)


# --- Reference tables ---

@router.get("/planets")
async def get_planets(session: AsyncSession = Depends(get_db)):
    """All planets (Sun, Moon, Mercury, etc.)."""
    rows = (await session.execute(select(Planet))).scalars().all()
    return [{"id": r.id, "name": r.name, "symbol": r.symbol, "description": r.description, "keywords": r.keywords} for r in rows]


@router.patch("/planets/{id}")
async def patch_planet(id: int, body: PlanetUpdate, session: AsyncSession = Depends(get_db)):
    """Update a planet by id."""
    row = (await session.execute(select(Planet).where(Planet.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Planet not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "name": row.name, "symbol": row.symbol, "description": row.description, "keywords": row.keywords}


@router.get("/signs")
async def get_signs(session: AsyncSession = Depends(get_db)):
    """All zodiac signs."""
    rows = (await session.execute(select(Sign))).scalars().all()
    return [
        {
            "id": r.id, "name": r.name, "element": r.element, "modality": r.modality,
            "archetypes_balanced": r.archetypes_balanced, "archetypes_unbalanced": r.archetypes_unbalanced,
            "journey": r.journey, "gifts": r.gifts, "challenges": r.challenges, "interpretation": r.interpretation,
            "adverb": r.adverb,
        }
        for r in rows
    ]


@router.patch("/signs/{id}")
async def patch_sign(id: int, body: SignUpdate, session: AsyncSession = Depends(get_db)):
    """Update a sign by id."""
    row = (await session.execute(select(Sign).where(Sign.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Sign not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {
        "id": row.id, "name": row.name, "element": row.element, "modality": row.modality,
        "archetypes_balanced": row.archetypes_balanced, "archetypes_unbalanced": row.archetypes_unbalanced,
        "journey": row.journey, "gifts": row.gifts, "challenges": row.challenges, "interpretation": row.interpretation,
        "adverb": row.adverb,
    }


@router.get("/houses")
async def get_houses(session: AsyncSession = Depends(get_db)):
    """All houses (1-12)."""
    rows = (await session.execute(select(House))).scalars().all()
    return [{"id": r.id, "number": r.number, "type": r.type_, "description": r.description, "subtitle": r.subtitle, "keywords": r.keywords} for r in rows]


@router.patch("/houses/{id}")
async def patch_house(id: int, body: HouseUpdate, session: AsyncSession = Depends(get_db)):
    """Update a house by id."""
    row = (await session.execute(select(House).where(House.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "House not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "number": row.number, "type": row.type_, "description": row.description, "subtitle": row.subtitle, "keywords": row.keywords}


@router.get("/aspects")
async def get_aspects(session: AsyncSession = Depends(get_db)):
    """All aspect types (Conjunction, Opposition, etc.)."""
    rows = (await session.execute(select(Aspect))).scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "angle_degrees": r.angle_degrees,
            "symbol": r.symbol,
            "type": r.type_,
            "summary_keyphrase": r.summary_keyphrase,
        }
        for r in rows
    ]


@router.patch("/aspects/{id}")
async def patch_aspect(id: int, body: AspectUpdate, session: AsyncSession = Depends(get_db)):
    """Update an aspect by id."""
    row = (await session.execute(select(Aspect).where(Aspect.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Aspect not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {
        "id": row.id,
        "name": row.name,
        "angle_degrees": row.angle_degrees,
        "symbol": row.symbol,
        "type": row.type_,
        "summary_keyphrase": row.summary_keyphrase,
    }


# --- Big Three: Moon and Ascendant from dedicated tables; Sun from signs (merged) ---

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


@router.patch("/moon/{id}")
async def patch_moon_interpretation(id: int, body: MoonSignInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a Moon sign interpretation by id."""
    row = (await session.execute(select(MoonSignInterpretation).where(MoonSignInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Moon sign interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    sign_name = (await session.execute(select(Sign.name).where(Sign.id == row.sign_id))).scalar_one()
    return {"id": row.id, "sign": sign_name, "sign_id": row.sign_id, "nature": row.nature, "sources_of_contentment": row.sources_of_contentment, "keywords": row.keywords, "interpretation": row.interpretation}


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


@router.patch("/ascendant/{id}")
async def patch_ascendant_interpretation(id: int, body: AscendantSignInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update an Ascendant sign interpretation by id."""
    row = (await session.execute(select(AscendantSignInterpretation).where(AscendantSignInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Ascendant sign interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    sign_name = (await session.execute(select(Sign.name).where(Sign.id == row.sign_id))).scalar_one()
    return {"id": row.id, "sign": sign_name, "sign_id": row.sign_id, "impression": row.impression, "appearance": row.appearance, "childhood": row.childhood, "balance": row.balance, "interpretation": row.interpretation}


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


@router.patch("/planet-sign/{id}")
async def patch_planet_sign_interpretation(id: int, body: PlanetSignInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a planet-sign interpretation by id."""
    row = (await session.execute(select(PlanetSignInterpretation).where(PlanetSignInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Planet-sign interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    planet_name = (await session.execute(select(Planet.name).where(Planet.id == row.planet_id))).scalar_one()
    sign_name = (await session.execute(select(Sign.name).where(Sign.id == row.sign_id))).scalar_one()
    return {"id": row.id, "planet": planet_name, "sign": sign_name, "interpretation_text": row.interpretation_text, "interpretation_long": row.interpretation_long, "interpretation_short": row.interpretation_short, "keywords": row.keywords, "retrograde_interpretation": row.retrograde_interpretation}


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


@router.patch("/planet-house/{id}")
async def patch_planet_house_interpretation(id: int, body: PlanetHouseInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a planet-house interpretation by id."""
    row = (await session.execute(select(PlanetHouseInterpretation).where(PlanetHouseInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Planet-house interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    planet_name = (await session.execute(select(Planet.name).where(Planet.id == row.planet_id))).scalar_one()
    house_num = (await session.execute(select(House.number).where(House.id == row.house_id))).scalar_one()
    return {"id": row.id, "planet": planet_name, "house": house_num, "interpretation_text": row.interpretation_text, "short_interpretation": row.short_interpretation, "retrograde_interpretation": row.retrograde_interpretation}


@router.get("/aspect-type")
async def get_aspect_type_interpretations(session: AsyncSession = Depends(get_db)):
    """Interpretations by aspect type (conjunction, stressful, easy-flowing)."""
    rows = (await session.execute(select(AspectTypeInterpretation))).scalars().all()
    return [{"id": r.id, "type_key": r.type_key, "interpretation_text": r.interpretation_text} for r in rows]


@router.patch("/aspect-type/{id}")
async def patch_aspect_type_interpretation(id: int, body: AspectTypeInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update an aspect type interpretation by id."""
    row = (await session.execute(select(AspectTypeInterpretation).where(AspectTypeInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Aspect type interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "type_key": row.type_key, "interpretation_text": row.interpretation_text}


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


@router.patch("/aspect-generic/{id}")
async def patch_aspect_interpretation(id: int, body: AspectInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a generic aspect interpretation by id."""
    row = (await session.execute(select(AspectInterpretation).where(AspectInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Aspect interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    aspect_name = (await session.execute(select(Aspect.name).where(Aspect.id == row.aspect_id))).scalar_one()
    return {"id": row.id, "aspect": aspect_name, "interpretation_text": row.interpretation_text}


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


@router.patch("/planet-aspect/{id}")
async def patch_planet_aspect_interpretation(id: int, body: PlanetAspectInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a planet-aspect interpretation by id."""
    row = (await session.execute(select(PlanetAspectInterpretation).where(PlanetAspectInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Planet-aspect interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    P1, P2 = aliased(Planet), aliased(Planet)
    p1_name = (await session.execute(select(Planet.name).where(Planet.id == row.planet_1_id))).scalar_one()
    p2_name = (await session.execute(select(Planet.name).where(Planet.id == row.planet_2_id))).scalar_one()
    aspect_name = (await session.execute(select(Aspect.name).where(Aspect.id == row.aspect_id))).scalar_one()
    return {"id": row.id, "planet_1": p1_name, "planet_2": p2_name, "aspect": aspect_name, "interpretation_text": row.interpretation_text}


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


@router.patch("/sign-house/{id}")
async def patch_sign_house_interpretation(id: int, body: SignHouseInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a sign-house interpretation by id."""
    row = (await session.execute(select(SignHouseInterpretation).where(SignHouseInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Sign-house interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    house_num = (await session.execute(select(House.number).where(House.id == row.house_id))).scalar_one()
    sign_name = (await session.execute(select(Sign.name).where(Sign.id == row.sign_id))).scalar_one()
    return {"id": row.id, "house": house_num, "sign": sign_name, "interpretation_text": row.interpretation_text}


@router.get("/chart-shape")
async def get_chart_shape_interpretations(session: AsyncSession = Depends(get_db)):
    """Chart shape interpretations (splash, bundle, bowl, etc.)."""
    rows = (await session.execute(select(ChartShapeInterpretation))).scalars().all()
    return [{"id": r.id, "shape_key": r.shape_key, "interpretation_text": r.interpretation_text} for r in rows]


@router.patch("/chart-shape/{id}")
async def patch_chart_shape_interpretation(id: int, body: ChartShapeInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a chart shape interpretation by id."""
    row = (await session.execute(select(ChartShapeInterpretation).where(ChartShapeInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Chart shape interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "shape_key": row.shape_key, "interpretation_text": row.interpretation_text}


@router.get("/chart-distribution")
async def get_chart_distribution_interpretations(session: AsyncSession = Depends(get_db)):
    """Hemisphere/quadrant distribution interpretations."""
    rows = (await session.execute(select(ChartDistributionInterpretation))).scalars().all()
    return [{"id": r.id, "distribution_key": r.distribution_key, "interpretation_text": r.interpretation_text} for r in rows]


@router.patch("/chart-distribution/{id}")
async def patch_chart_distribution_interpretation(id: int, body: ChartDistributionInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a chart distribution interpretation by id."""
    row = (await session.execute(select(ChartDistributionInterpretation).where(ChartDistributionInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Chart distribution interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "distribution_key": row.distribution_key, "interpretation_text": row.interpretation_text}


@router.get("/modality-element")
async def get_modality_element_interpretations(session: AsyncSession = Depends(get_db)):
    """Modality and element distribution interpretations."""
    rows = (await session.execute(select(ModalityElementDistributionInterpretation))).scalars().all()
    return [{"id": r.id, "distribution_key": r.distribution_key, "interpretation_text": r.interpretation_text} for r in rows]


@router.patch("/modality-element/{id}")
async def patch_modality_element_interpretation(id: int, body: ModalityElementDistributionInterpretationUpdate, session: AsyncSession = Depends(get_db)):
    """Update a modality-element interpretation by id."""
    row = (await session.execute(select(ModalityElementDistributionInterpretation).where(ModalityElementDistributionInterpretation.id == id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Modality-element interpretation not found")
    _apply_update(row, body)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "distribution_key": row.distribution_key, "interpretation_text": row.interpretation_text}
