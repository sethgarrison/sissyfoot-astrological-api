import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from kerykeion import AstrologicalSubject
from kerykeion.aspects import AspectsFactory
from typing import Optional

app = FastAPI(
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


class NatalChart(BaseModel):
    name: Optional[str] = None
    birth_datetime: str
    latitude: float
    longitude: float
    sun_sign: str
    moon_sign: str
    rising_sign: str
    lunar_phase: LunarPhase
    planets: list[PlanetPosition]
    houses: list[HouseCusp]
    aspects: list[AspectInfo]


def _sign(abbr: str) -> str:
    return SIGN_FULL.get(abbr, abbr)


def _house_num(house_str: str) -> int:
    return HOUSE_NUM.get(house_str, 0)


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


def build_chart(
    year: int, month: int, day: int, hour: int, minute: int,
    *,
    city: Optional[str] = None,
    nation: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    tz_str: Optional[str] = None,
    name: str = "",
) -> NatalChart:
    kwargs: dict = dict(online=False) if (lat and lng and tz_str) else {}
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
    for node_attr in ("true_north_lunar_node", "true_south_lunar_node"):
        node = getattr(subject, node_attr, None)
        if node is not None:
            bodies.append(node)

    planets = [_planet(b) for b in bodies]

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
        sun_sign=_sign(subject.sun.sign),
        moon_sign=_sign(subject.moon.sign),
        rising_sign=_sign(subject.first_house.sign),
        lunar_phase=lunar_phase,
        planets=planets,
        houses=houses,
        aspects=aspects,
    )


@app.get("/chart", response_model=NatalChart, summary="Generate a natal chart")
def get_chart(
    year: int = Query(..., examples=[1990], description="Birth year"),
    month: int = Query(..., ge=1, le=12, examples=[6], description="Birth month"),
    day: int = Query(..., ge=1, le=31, examples=[15], description="Birth day"),
    hour: int = Query(12, ge=0, le=23, description="Birth hour (24h format)"),
    minute: int = Query(0, ge=0, le=59, description="Birth minute"),
    city: Optional[str] = Query(None, examples=["New York"], description="Birth city (used for geocoding if lat/lng/tz_str not given)"),
    nation: Optional[str] = Query(None, examples=["US"], description="Birth nation ISO code (used with city)"),
    lat: Optional[float] = Query(None, examples=[40.7128], description="Latitude (skip geocoding)"),
    lng: Optional[float] = Query(None, examples=[-74.006], description="Longitude (skip geocoding)"),
    tz_str: Optional[str] = Query(None, examples=["America/New_York"], description="IANA timezone (required with lat/lng)"),
    name: Optional[str] = Query(None, description="Optional name for the subject"),
):
    """
    Generate a natal chart. Provide either `city`+`nation` for automatic geocoding
    (requires GEONAMES_USERNAME env var) or `lat`+`lng`+`tz_str` for direct coordinates.
    """
    if not (lat and lng and tz_str) and not city:
        raise HTTPException(
            status_code=400,
            detail="Provide either city+nation or lat+lng+tz_str.",
        )
    try:
        return build_chart(
            year, month, day, hour, minute,
            city=city, nation=nation, lat=lat, lng=lng, tz_str=tz_str,
            name=name or "",
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


class ChartRequest(BaseModel):
    year: int = Field(..., examples=[1990])
    month: int = Field(..., ge=1, le=12, examples=[6])
    day: int = Field(..., ge=1, le=31, examples=[15])
    hour: int = Field(12, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    city: Optional[str] = Field(None, examples=["New York"])
    nation: Optional[str] = Field(None, examples=["US"])
    lat: Optional[float] = Field(None, examples=[40.7128])
    lng: Optional[float] = Field(None, examples=[-74.006])
    tz_str: Optional[str] = Field(None, examples=["America/New_York"])
    name: Optional[str] = None


@app.post("/chart", response_model=NatalChart, summary="Generate a natal chart (POST)")
def create_chart(req: ChartRequest):
    """Generate a natal chart via POST body."""
    if not (req.lat and req.lng and req.tz_str) and not req.city:
        raise HTTPException(
            status_code=400,
            detail="Provide either city+nation or lat+lng+tz_str.",
        )
    try:
        return build_chart(
            req.year, req.month, req.day, req.hour, req.minute,
            city=req.city, nation=req.nation,
            lat=req.lat, lng=req.lng, tz_str=req.tz_str,
            name=req.name or "",
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
