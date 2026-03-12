import os
import re
from fastapi import FastAPI, HTTPException, Query, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from kerykeion import AstrologicalSubject
from kerykeion.aspects import AspectsFactory
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db, init_db
from database.models import Reading
from interpretations.chart_shapes import detect_chart_shape, detect_distributions
from interpretations.modality_element import detect_modality_element_keys
from interpretations.defaults import (
    get_default_planet_in_sign,
    get_default_planet_in_house,
    get_default_aspects,
)
from interpretations.lookup import fetch_interpretations


async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Natal Chart API",
    description="Generate natal (birth) charts powered by the Swiss Ephemeris via Kerykeion.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SIGN_FULL = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces",
}

# Sign → element (fire, earth, air, water) and quality/modality (cardinal, fixed, mutable)
SIGN_TO_ELEMENT = {
    "Aries": "fire", "Taurus": "earth", "Gemini": "air", "Cancer": "water",
    "Leo": "fire", "Virgo": "earth", "Libra": "air", "Scorpio": "water",
    "Sagittarius": "fire", "Capricorn": "earth", "Aquarius": "air", "Pisces": "water",
}
SIGN_TO_QUALITY = {
    "Aries": "cardinal", "Taurus": "fixed", "Gemini": "mutable", "Cancer": "cardinal",
    "Leo": "fixed", "Virgo": "mutable", "Libra": "cardinal", "Scorpio": "fixed",
    "Sagittarius": "mutable", "Capricorn": "cardinal", "Aquarius": "fixed", "Pisces": "mutable",
}

HOUSE_NUM = {
    "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
    "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
    "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12,
}

HOUSE_ATTRS = [
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
]

# House system: API value -> Kerykeion identifier (P=Placidus, W=Whole Sign)
HOUSE_SYSTEMS = {"whole_sign": "W", "placidus": "P", "WSH": "W"}
DEFAULT_HOUSE_SYSTEM = "whole_sign"


def _compute_sign_placement_overview(planets: list["PlanetPosition"]) -> "SignPlacementOverview":
    """Compute sign distribution from planetary placements: which signs have planets, by quality and element."""
    signs_with_planets: dict[str, list[str]] = {}
    by_quality: dict[str, list[str]] = {"cardinal": [], "fixed": [], "mutable": []}  # signs per quality
    by_element: dict[str, list[str]] = {"fire": [], "earth": [], "air": [], "water": []}  # signs per element
    quality_planets: dict[str, list[str]] = {"cardinal": [], "fixed": [], "mutable": []}
    element_planets: dict[str, list[str]] = {"fire": [], "earth": [], "air": [], "water": []}
    for p in planets:
        sign = p.sign
        signs_with_planets.setdefault(sign, []).append(p.name)
        q = SIGN_TO_QUALITY.get(sign)
        if q:
            if sign not in by_quality[q]:
                by_quality[q].append(sign)
            quality_planets[q].append(p.name)
        e = SIGN_TO_ELEMENT.get(sign)
        if e:
            if sign not in by_element[e]:
                by_element[e].append(sign)
            element_planets[e].append(p.name)
    return SignPlacementOverview(
        signs_with_planets=signs_with_planets,
        by_quality={
            k: QualityDistribution(count=len(quality_planets[k]), signs=v, planets=quality_planets[k])
            for k, v in by_quality.items()
        },
        by_element={
            k: ElementDistribution(count=len(element_planets[k]), signs=v, planets=element_planets[k])
            for k, v in by_element.items()
        },
    )


class PlanetPosition(BaseModel):
    name: str
    sign: str
    sign_num: int
    degree: float
    abs_degree: float
    house: int
    retrograde: bool
    speed: Optional[float] = None


class HouseCusp(BaseModel):
    number: int
    sign: str
    degree: float
    abs_degree: float


class LunarNodePosition(BaseModel):
    """North or South Lunar Node — modeled separately from planets (no aspects, no chart shape)."""
    node: str  # "North Node" | "South Node"
    sign: str
    sign_num: int
    degree: float
    abs_degree: float
    house: int


class AspectInfo(BaseModel):
    planet1: str
    planet2: str
    aspect: str
    aspect_degrees: int
    orbit: float
    movement: Optional[str] = None


class LunarPhase(BaseModel):
    degrees_between: float
    phase_name: str
    emoji: str


class ChartShapeInfo(BaseModel):
    primary: Optional[str] = None
    interpretation: Optional[str] = None
    distribution: dict[str, str] = {}


class QualityDistribution(BaseModel):
    """Count and list of signs/planets for a quality (cardinal, fixed, mutable)."""
    count: int
    signs: list[str] = []  # signs with planets in this quality
    planets: list[str] = []  # planet names in signs of this quality


class ElementDistribution(BaseModel):
    """Count and list of signs/planets for an element (fire, earth, air, water)."""
    count: int
    signs: list[str] = []  # signs with planets in this element
    planets: list[str] = []  # planet names in signs of this element


class SignPlacementOverview(BaseModel):
    """Overview of signs that have planets, with distributions by quality and element."""
    signs_with_planets: dict[str, list[str]] = {}  # sign -> list of planet names
    by_quality: dict[str, QualityDistribution] = {}  # cardinal, fixed, mutable
    by_element: dict[str, ElementDistribution] = {}  # fire, earth, air, water


class ChartInterpretations(BaseModel):
    planet_in_sign: dict[str, str] = {}
    planet_in_house: dict[str, str] = {}
    aspects: dict[str, str] = {}
    chart_shape: ChartShapeInfo = ChartShapeInfo()
    modality_element_distribution: dict[str, str] = {}  # e.g. element_fire_dominant -> interpretation
    retrograde_planets: list[str] = []  # planet names that are retrograde in this chart
    retrograde_interpretations: dict[str, str] = {}  # e.g. "Mercury in Gemini" -> retrograde meaning


class NatalChart(BaseModel):
    name: Optional[str] = None
    birth_datetime: str
    latitude: float
    longitude: float
    house_system: str = "whole_sign"  # whole_sign (default) or placidus
    sun_sign: str
    moon_sign: str
    rising_sign: str
    lunar_phase: LunarPhase
    planets: list[PlanetPosition]
    lunar_nodes: list[LunarNodePosition] = []  # North & South Node (excluded from aspects & chart shape)
    houses: list[HouseCusp]
    houses_overview: SignPlacementOverview = Field(
        default_factory=lambda: SignPlacementOverview(),
        description="Overview of signs that have planets, with distributions by quality and element",
    )
    aspects: list[AspectInfo]
    interpretations: ChartInterpretations = ChartInterpretations()
    reading_id: Optional[str] = None  # Use this to fetch via GET /readings/{reading_id}


# Delimiter for reading identifier (URL-safe, avoids conflict with negative numbers)
READING_ID_DELIM = "__"


def _make_reading_identifier(name: str, birth_datetime: str, lat: float, lng: float) -> str:
    """Build identifier: name-birthdatetime-lat-long (using __ as delimiter for clarity)."""
    safe_name = (name or "Subject").strip().replace(" ", "_")
    safe_name = re.sub(r"[^\w\-]", "", safe_name) or "Subject"
    return f"{safe_name}{READING_ID_DELIM}{birth_datetime}{READING_ID_DELIM}{lat}{READING_ID_DELIM}{lng}"


def _sign(abbr: str) -> str:
    return SIGN_FULL.get(abbr, abbr)


def _house_num(house_str: str) -> int:
    return HOUSE_NUM.get(house_str, 0)


def _parse_time(time_str: Optional[str]) -> Optional[tuple[int, int]]:
    """
    Parse time string into (hour, minute). Accepts:
    - "HH:MM" (e.g. "14:30")
    - "HH:MM:SS" (e.g. "14:30:00")
    - "H:MM" (e.g. "9:05")
    Returns None if invalid or empty.
    """
    if not time_str or not time_str.strip():
        return None
    parts = time_str.strip().split(":")
    if len(parts) < 2:
        return None
    try:
        h = int(parts[0])
        m = int(parts[1])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return (h, m)
    except ValueError:
        pass
    return None


def _planet(body) -> PlanetPosition:
    return PlanetPosition(
        name=body.name.replace("_", " "),
        sign=_sign(body.sign),
        sign_num=body.sign_num,
        degree=round(body.position, 4),
        abs_degree=round(body.abs_pos, 4),
        house=_house_num(body.house),
        retrograde=body.retrograde or False,
        speed=round(body.speed, 6) if body.speed else None,
    )


def _lunar_node(body, label: str) -> LunarNodePosition:
    return LunarNodePosition(
        node=label,
        sign=_sign(body.sign),
        sign_num=body.sign_num,
        degree=round(body.position, 4),
        abs_degree=round(body.abs_pos, 4),
        house=_house_num(body.house),
    )


NODE_NAMES = {"True_North_Lunar_Node", "True_South_Lunar_Node", "North_Node", "South_Node"}  # Kerykeion aspect names


def build_chart(
    year: int, month: int, day: int, hour: int, minute: int,
    *,
    city: Optional[str] = None,
    nation: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    tz_str: Optional[str] = None,
    name: str = "",
    house_system: str = DEFAULT_HOUSE_SYSTEM,
) -> NatalChart:
    house_sys = HOUSE_SYSTEMS.get(house_system, HOUSE_SYSTEMS[DEFAULT_HOUSE_SYSTEM])
    kwargs: dict = {"houses_system_identifier": house_sys}
    if lat and lng and tz_str:
        kwargs["online"] = False
    subject = AstrologicalSubject(
        name or "Subject", year, month, day, hour, minute,
        city=city, nation=nation, lat=lat, lng=lng, tz_str=tz_str,
        geonames_username=os.environ.get("GEONAMES_USERNAME"),
        **kwargs,
    )

    bodies = [
        subject.sun, subject.moon, subject.mercury, subject.venus,
        subject.mars, subject.jupiter, subject.saturn, subject.uranus,
        subject.neptune, subject.pluto, subject.chiron,
    ]
    planets = [_planet(b) for b in bodies]

    lunar_nodes = []
    north = getattr(subject, "true_north_lunar_node", None)
    south = getattr(subject, "true_south_lunar_node", None)
    if north is not None:
        lunar_nodes.append(_lunar_node(north, "North Node"))
    if south is not None:
        lunar_nodes.append(_lunar_node(south, "South Node"))

    houses = []
    for i, attr in enumerate(HOUSE_ATTRS, start=1):
        h = getattr(subject, attr)
        houses.append(HouseCusp(
            number=i,
            sign=_sign(h.sign),
            degree=round(h.position, 4),
            abs_degree=round(h.abs_pos, 4),
        ))

    aspects = []
    try:
        asp_result = AspectsFactory.natal_aspects(subject._model)
        for a in asp_result.aspects:
            # Exclude aspects involving lunar nodes (they're not planets)
            if a.p1_name in NODE_NAMES or a.p2_name in NODE_NAMES:
                continue
            aspects.append(AspectInfo(
                planet1=a.p1_name.replace("_", " "),
                planet2=a.p2_name.replace("_", " "),
                aspect=a.aspect,
                aspect_degrees=a.aspect_degrees,
                orbit=round(a.orbit, 4),
                movement=a.aspect_movement,
            ))
    except Exception:
        pass

    lp = subject._model.lunar_phase
    lunar_phase = LunarPhase(
        degrees_between=round(lp.degrees_between_s_m, 4),
        phase_name=lp.moon_phase_name,
        emoji=lp.moon_emoji,
    )

    return NatalChart(
        name=name or None,
        birth_datetime=f"{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}",
        latitude=subject.lat,
        longitude=subject.lng,
        house_system=house_system,
        sun_sign=_sign(subject.sun.sign),
        moon_sign=_sign(subject.moon.sign),
        rising_sign=_sign(subject.first_house.sign),
        lunar_phase=lunar_phase,
        planets=planets,
        lunar_nodes=lunar_nodes,
        houses=houses,
        houses_overview=_compute_sign_placement_overview(planets),
        aspects=aspects,
        interpretations=ChartInterpretations(),
    )


async def _enrich_with_interpretations(
    chart: NatalChart, session: AsyncSession
) -> NatalChart:
    """Fetch interpretations from DB and attach to chart."""
    planet_sign_pairs = [(p.name, p.sign) for p in chart.planets]
    planet_house_pairs = [(p.name, p.house) for p in chart.planets]
    aspect_keys = [f"{a.planet1} {a.aspect} {a.planet2}" for a in chart.aspects]
    planet_dicts = [
        {"name": p.name, "abs_degree": p.abs_degree, "house": p.house}
        for p in chart.planets
    ]
    chart_shape = detect_chart_shape(planet_dicts)
    distribution_keys = detect_distributions(planet_dicts)
    by_quality = {k: v.count for k, v in chart.houses_overview.by_quality.items()}
    by_element = {k: v.count for k, v in chart.houses_overview.by_element.items()}
    modality_element_keys = detect_modality_element_keys(by_quality, by_element)
    retrograde_planets = {p.name for p in chart.planets if p.retrograde}
    try:
        interp = await fetch_interpretations(
            session,
            planet_sign_pairs=planet_sign_pairs,
            planet_house_pairs=planet_house_pairs,
            aspect_keys=aspect_keys,
            chart_shape=chart_shape,
            distribution_keys=distribution_keys,
            modality_element_keys=modality_element_keys,
            retrograde_planets=retrograde_planets,
        )
        planet_in_sign = dict(interp["planet_in_sign"])
    except Exception:
        planet_in_sign = {}
        interp = {
            "planet_in_house": {},
            "aspects": {},
            "chart_shape": {"primary": chart_shape, "interpretation": None, "distribution": {}},
            "modality_element_distribution": {},
            "retrograde_planets": sorted(retrograde_planets),
            "retrograde_interpretations": {},
        }

    # Merge built-in defaults for Sun, Moon, Rising (always include when missing)
    for key, text in get_default_planet_in_sign(
        chart.sun_sign, chart.moon_sign, chart.rising_sign
    ).items():
        if key not in planet_in_sign:
            planet_in_sign[key] = text

    # Merge built-in defaults for planet-in-house and aspects
    planet_in_house = dict(interp.get("planet_in_house", {}))
    for key, text in get_default_planet_in_house(planet_house_pairs).items():
        if key not in planet_in_house:
            planet_in_house[key] = text

    aspects = dict(interp.get("aspects", {}))
    for key, text in get_default_aspects(aspect_keys).items():
        if key not in aspects:
            aspects[key] = text

    chart.interpretations = ChartInterpretations(
        planet_in_sign=planet_in_sign,
        planet_in_house=planet_in_house,
        aspects=aspects,
        chart_shape=ChartShapeInfo(
            primary=interp.get("chart_shape", {}).get("primary"),
            interpretation=interp.get("chart_shape", {}).get("interpretation"),
            distribution=interp.get("chart_shape", {}).get("distribution", {}),
        ),
        modality_element_distribution=interp.get("modality_element_distribution", {}),
        retrograde_planets=interp.get("retrograde_planets", []),
        retrograde_interpretations=interp.get("retrograde_interpretations", {}),
    )
    return chart


async def _save_reading(chart: NatalChart, session: AsyncSession) -> None:
    """Save chart to readings table. Upserts by identifier."""
    identifier = _make_reading_identifier(
        chart.name or "Subject",
        chart.birth_datetime,
        chart.latitude,
        chart.longitude,
    )
    chart_json = chart.model_dump_json()
    existing = (
        await session.execute(select(Reading).where(Reading.identifier == identifier))
    ).scalar_one_or_none()
    if existing:
        existing.chart_data = chart_json
    else:
        session.add(Reading(identifier=identifier, chart_data=chart_json))
    await session.flush()


@app.get("/chart", response_model=NatalChart, summary="Generate a natal chart")
async def get_chart(
    year: int = Query(..., examples=[1990], description="Birth year"),
    month: int = Query(..., ge=1, le=12, examples=[6], description="Birth month"),
    day: int = Query(..., ge=1, le=31, examples=[15], description="Birth day"),
    hour: int = Query(12, ge=0, le=23, description="Birth hour (24h format)"),
    minute: int = Query(0, ge=0, le=59, description="Birth minute"),
    time: Optional[str] = Query(
        None,
        description="Alternative: birth time as HH:MM or HH:MM:SS (overrides hour and minute)",
        examples=["14:30"],
    ),
    city: Optional[str] = Query(None, examples=["New York"], description="Birth city (used for geocoding if lat/lng/tz_str not given)"),
    nation: Optional[str] = Query(None, examples=["US"], description="Birth nation ISO code (used with city)"),
    lat: Optional[float] = Query(None, examples=[40.7128], description="Latitude (skip geocoding)"),
    lng: Optional[float] = Query(None, examples=[-74.006], description="Longitude (skip geocoding)"),
    tz_str: Optional[str] = Query(None, examples=["America/New_York"], description="IANA timezone (required with lat/lng)"),
    name: Optional[str] = Query(None, description="Optional name for the subject"),
    house_system: str = Query(
        DEFAULT_HOUSE_SYSTEM,
        description="House system: whole_sign (default) or placidus",
        examples=["whole_sign"],
    ),
    session: AsyncSession = Depends(get_db),
):
    """
    Generate a natal chart. Provide either `city`+`nation` for automatic geocoding
    (requires GEONAMES_USERNAME env var) or `lat`+`lng`+`tz_str` for direct coordinates.
    Interpretations are loaded from the database when available.
    """
    if not (lat and lng and tz_str) and not city:
        raise HTTPException(
            status_code=400,
            detail="Provide either city+nation or lat+lng+tz_str.",
        )
    # time param overrides hour/minute when provided (e.g. "14:30")
    if (parsed := _parse_time(time)):
        hour, minute = parsed
    try:
        chart = build_chart(
            year, month, day, hour, minute,
            city=city, nation=nation, lat=lat, lng=lng, tz_str=tz_str,
            name=name or "",
            house_system=house_system,
        )
        chart = await _enrich_with_interpretations(chart, session)
        chart.reading_id = _make_reading_identifier(
            chart.name or "Subject", chart.birth_datetime, chart.latitude, chart.longitude
        )
        await _save_reading(chart, session)
        return chart
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


class ChartRequest(BaseModel):
    year: int = Field(..., examples=[1990])
    month: int = Field(..., ge=1, le=12, examples=[6])
    day: int = Field(..., ge=1, le=31, examples=[15])
    hour: int = Field(12, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    time: Optional[str] = Field(
        None,
        description="Alternative: birth time as HH:MM or HH:MM:SS (overrides hour and minute)",
    )
    city: Optional[str] = Field(None, examples=["New York"])
    nation: Optional[str] = Field(None, examples=["US"])
    lat: Optional[float] = Field(None, examples=[40.7128])
    lng: Optional[float] = Field(None, examples=[-74.006])
    tz_str: Optional[str] = Field(None, examples=["America/New_York"])
    name: Optional[str] = None
    house_system: str = Field(DEFAULT_HOUSE_SYSTEM, description="whole_sign or placidus")


@app.post("/chart", response_model=NatalChart, summary="Generate a natal chart (POST)")
async def create_chart(
    req: ChartRequest,
    session: AsyncSession = Depends(get_db),
):
    """Generate a natal chart via POST body."""
    if not (req.lat and req.lng and req.tz_str) and not req.city:
        raise HTTPException(
            status_code=400,
            detail="Provide either city+nation or lat+lng+tz_str.",
        )
    try:
        hour, minute = req.hour, req.minute
        if (parsed := _parse_time(req.time)):
            hour, minute = parsed
        chart = build_chart(
            req.year, req.month, req.day, hour, minute,
            city=req.city, nation=req.nation,
            lat=req.lat, lng=req.lng, tz_str=req.tz_str,
            name=req.name or "",
            house_system=req.house_system,
        )
        chart = await _enrich_with_interpretations(chart, session)
        chart.reading_id = _make_reading_identifier(
            chart.name or "Subject", chart.birth_datetime, chart.latitude, chart.longitude
        )
        await _save_reading(chart, session)
        return chart
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


class ReadingSummary(BaseModel):
    identifier: str
    name: Optional[str] = None
    birth_datetime: str
    created_at: Optional[str] = None


@app.get("/readings", summary="List all saved readings")
async def list_readings(session: AsyncSession = Depends(get_db)):
    """Return all saved readings. Full chart data available at GET /readings/{identifier}."""
    rows = (await session.execute(select(Reading).order_by(Reading.created_at.desc()))).scalars().all()
    result = []
    for r in rows:
        chart = NatalChart.model_validate_json(r.chart_data)
        result.append(
            ReadingSummary(
                identifier=r.identifier,
                name=chart.name,
                birth_datetime=chart.birth_datetime,
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
        )
    return result


@app.get("/readings/{identifier}", response_model=NatalChart, summary="Fetch a saved reading")
async def get_reading(
    identifier: str = Path(..., description="Reading ID: name__birthdatetime__lat__lng"),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve a previously saved natal chart reading by its identifier."""
    row = (
        await session.execute(select(Reading).where(Reading.identifier == identifier))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Reading not found")
    chart = NatalChart.model_validate_json(row.chart_data)
    chart.reading_id = identifier
    return chart


@app.get("/health")
def health():
    return {"status": "ok"}
