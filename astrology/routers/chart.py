import os
import re
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from astrology.logic.pipeline import (
    DEFAULT_HOUSE_SYSTEM,
    build_chart_api_response,
    build_chart_core,
)
from astrology.db.models import (
    Aspect,
    AscendantSignInterpretation,
    AspectInterpretation,
    AspectTypeInterpretation,
    ChartDistributionInterpretation,
    ChartShapeInterpretation,
    House,
    ModalityElementDistributionInterpretation,
    MoonSignInterpretation,
    Planet,
    PlanetAspectInterpretation,
    PlanetHouseInterpretation,
    PlanetSignInterpretation,
    Reading,
    Sign,
    SignHouseInterpretation,
)
from astrology.logic.interpretations.data_quality import is_placeholder_text
from astrology.schema.chart_response import ChartAPIResponse
from core.db import get_db

router = APIRouter(tags=["astrology"])


class LocationResult(BaseModel):
    """Single location from /locations search for autocomplete."""

    display: str  # Human-readable label for dropdown (e.g. "Laurel, Mississippi, United States")
    city: str  # Exact string for chart API city param (e.g. "Laurel,MS")
    nation: str  # ISO country code (e.g. "US")
    timezone: str  # IANA timezone (e.g. "America/Chicago")
    lat: float  # Latitude — client can use lat+lng+timezone for chart API
    lng: float  # Longitude


READING_ID_DELIM = "__"


def _make_reading_identifier(name: str, birth_datetime: str, lat: float, lng: float) -> str:
    """Build identifier: name-birthdatetime-lat-long (using __ as delimiter for clarity)."""
    safe_name = (name or "Subject").strip().replace(" ", "_")
    safe_name = re.sub(r"[^\w\-]", "", safe_name) or "Subject"
    return f"{safe_name}{READING_ID_DELIM}{birth_datetime}{READING_ID_DELIM}{lat}{READING_ID_DELIM}{lng}"


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


GEONAMES_SEARCH = "https://secure.geonames.org/searchJSON"
GEONAMES_TIMEZONE = "https://secure.geonames.org/timezoneJSON"
_timezone_cache: dict[tuple[float, float], str] = {}


async def _search_locations(q: str, limit: int) -> list[LocationResult]:
    """
    Search GeoNames for places, fetch timezone per result.
    Requires GEONAMES_USERNAME env var. Returns [] on any failure (no 500).
    """
    try:
        username = os.environ.get("GEONAMES_USERNAME")
        if not username:
            return []
        q = (q or "").strip()
        if not q or len(q) < 2:
            return []
        limit = min(max(1, limit), 10)
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                GEONAMES_SEARCH,
                params={
                    "q": q,
                    "maxRows": limit,
                    "username": username,
                    "featureClass": "P",  # populated places
                },
            )
            r.raise_for_status()
            data = r.json()
        if not isinstance(data, dict):
            return []
        if data.get("status") and data["status"].get("value") not in (None, 0):
            return []
        geonames = data.get("geonames") or []
        results: list[LocationResult] = []
        for g in geonames:
            try:
                if not isinstance(g, dict):
                    continue
                name = g.get("name") or g.get("toponymName") or ""
                country_code = g.get("countryCode") or ""
                admin_code = g.get("adminCode1") or ""
                admin_name = g.get("adminName1") or ""
                country_name = g.get("countryName") or ""
                lat = float(g.get("lat", 0))
                lng = float(g.get("lng", 0))
                if not name or not country_code:
                    continue
                cache_key = (round(lat, 4), round(lng, 4))
                tz_str = _timezone_cache.get(cache_key)
                if tz_str is None:
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as tz_client:
                            tz_r = await tz_client.get(
                                GEONAMES_TIMEZONE,
                                params={"lat": lat, "lng": lng, "username": username},
                            )
                            tz_r.raise_for_status()
                            tz_data = tz_r.json()
                            tz_str = tz_data.get("timezoneId") or tz_data.get("timezone") or "UTC"
                    except Exception:
                        tz_str = "UTC"
                    _timezone_cache[cache_key] = tz_str
                city = f"{name},{admin_code}" if admin_code else name
                parts = [name]
                if admin_name:
                    parts.append(admin_name)
                if country_name:
                    parts.append(country_name)
                display = ", ".join(parts)
                results.append(
                    LocationResult(
                        display=display,
                        city=city,
                        nation=country_code,
                        timezone=tz_str,
                        lat=lat,
                        lng=lng,
                    )
                )
            except (ValueError, TypeError, KeyError):
                continue
        return results
    except Exception:
        return []


async def _save_reading(chart: ChartAPIResponse, session: AsyncSession) -> None:
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


@router.get("/locations", response_model=list[LocationResult], summary="Search locations for birth place")
async def get_locations(
    q: str = Query(..., min_length=2, description="Partial place name (e.g. Laurel, New York, London)"),
    limit: int = Query(10, ge=1, le=10, description="Max number of results"),
):
    """
    Search for places by name. Returns display label, city, nation, timezone, and lat/lng.
    Use for autocomplete — select a result to populate city, nation, and timezone (or lat+lng+timezone)
    for the chart API. Requires GEONAMES_USERNAME env var.
    """
    return await _search_locations(q, limit)


@router.get("/chart", response_model=ChartAPIResponse, summary="Generate a natal chart")
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
    if (parsed := _parse_time(time)):
        hour, minute = parsed
    try:
        core = build_chart_core(
            year, month, day, hour, minute,
            city=city, nation=nation, lat=lat, lng=lng, tz_str=tz_str,
            name=name or "",
            house_system=house_system,
        )
        chart = await build_chart_api_response(core, session)
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


@router.post("/chart", response_model=ChartAPIResponse, summary="Generate a natal chart (POST)")
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
        core = build_chart_core(
            req.year, req.month, req.day, hour, minute,
            city=req.city, nation=req.nation,
            lat=req.lat, lng=req.lng, tz_str=req.tz_str,
            name=req.name or "",
            house_system=req.house_system,
        )
        chart = await build_chart_api_response(core, session)
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


@router.get("/readings", summary="List all saved readings")
async def list_readings(session: AsyncSession = Depends(get_db)):
    """Return all saved readings. Full chart data available at GET /readings/{identifier}."""
    rows = (await session.execute(select(Reading).order_by(Reading.created_at.desc()))).scalars().all()
    result = []
    for r in rows:
        chart = ChartAPIResponse.model_validate_json(r.chart_data)
        result.append(
            ReadingSummary(
                identifier=r.identifier,
                name=chart.name or None,
                birth_datetime=chart.birth_datetime,
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
        )
    return result


@router.get("/readings/{identifier}", response_model=ChartAPIResponse, summary="Fetch a saved reading")
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
    chart = ChartAPIResponse.model_validate_json(row.chart_data)
    chart.reading_id = identifier
    return chart


@router.get("/debug/interpretations", summary="Debug: interpretation table row counts and sample lookups")
async def debug_interpretations(session: AsyncSession = Depends(get_db)):
    """
    Returns row counts for all interpretation tables and a sample lookup check.
    Use to verify interpretation tables are populated and lookups hit the DB vs defaults.
    """
    async def count(model):
        r = await session.execute(select(func.count()).select_from(model))
        return r.scalar() or 0

    counts = {
        "reference": {
            "planets": await count(Planet),
            "signs": await count(Sign),
            "houses": await count(House),
            "aspects": await count(Aspect),
        },
        "interpretations": {
            "planet_sign": await count(PlanetSignInterpretation),
            "planet_house": await count(PlanetHouseInterpretation),
            "sun_in_signs": len((await session.execute(select(Sign).where(Sign.archetypes_balanced.isnot(None)))).scalars().all()),
            "moon_sign_big_three": await count(MoonSignInterpretation),
            "ascendant_sign_big_three": await count(AscendantSignInterpretation),
            "aspect_type": await count(AspectTypeInterpretation),
            "aspect_generic": await count(AspectInterpretation),
            "planet_aspect": await count(PlanetAspectInterpretation),
            "sign_house": await count(SignHouseInterpretation),
            "chart_shape": await count(ChartShapeInterpretation),
            "chart_distribution": await count(ChartDistributionInterpretation),
            "modality_element": await count(ModalityElementDistributionInterpretation),
        },
    }

    sample_checks = {}
    sun_id = (await session.execute(select(Planet.id).where(Planet.name == "Sun"))).scalar_one_or_none()
    aries_id = (await session.execute(select(Sign.id).where(Sign.name == "Aries"))).scalar_one_or_none()
    if sun_id and aries_id:
        r = await session.execute(
            select(PlanetSignInterpretation.interpretation_text).where(
                PlanetSignInterpretation.planet_id == sun_id,
                PlanetSignInterpretation.sign_id == aries_id,
            )
        )
        row = r.one_or_none()
        sample_checks["Sun in Aries"] = {
            "in_db": row is not None,
            "is_placeholder": is_placeholder_text(row[0]) if row else None,
            "preview": (row[0][:80] + "…") if row and len(row[0]) > 80 else (row[0] if row else None),
        }

    all_psi = (await session.execute(select(PlanetSignInterpretation.interpretation_text))).scalars().all()
    placeholder_count = sum(1 for t in all_psi if is_placeholder_text(t or ""))
    sample_checks["planet_sign_placeholder_count"] = placeholder_count
    sample_checks["planet_sign_total"] = len(all_psi)
    sample_checks["planet_sign_with_real_content"] = len(all_psi) - placeholder_count

    interp = counts["interpretations"]
    gaps = []
    if interp.get("sun_in_signs", 0) == 0:
        gaps.append("Big Three (sun): sun data not loaded into signs table")
    if interp["moon_sign_big_three"] == 0:
        gaps.append("Big Three (moon): moon sign interpretations missing or empty")
    if interp["ascendant_sign_big_three"] == 0:
        gaps.append("Big Three (ascendant): ascendant sign interpretations missing or empty")
    if interp["sign_house"] == 0:
        gaps.append("Sign-house: no rows in sign_house_interpretations")
    if interp["planet_aspect"] == 0:
        gaps.append("Planet-aspect: no planet-pair rows in planet_aspect_interpretations")
    if placeholder_count > 0:
        gaps.append(f"planet_sign: {placeholder_count} rows still placeholders (e.g. Sun/Moon/Chiron missing in planet_sign_interpretations)")

    return {"counts": counts, "sample_checks": sample_checks, "likely_gaps": gaps}
