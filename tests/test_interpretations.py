"""
Test interpretation data structure, sources, and placeholder metadata.
Run: pytest tests/test_interpretations.py -v
Requires: database seeded (python -m database.seed, python -m database.seed_from_csv)
"""
import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from interpretations.data_quality import is_placeholder_text


# Birth data that produces a known chart (NYC, fixed for reproducibility)
CHART_PARAMS = {
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 12,
    "minute": 0,
    "lat": 40.7128,
    "lng": -74.006,
    "tz_str": "America/New_York",
}


@pytest.mark.asyncio
async def test_chart_returns_interpretation_structure():
    """Chart response includes all expected interpretation fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    interp = data.get("interpretations", {})
    assert "planet_in_sign" in interp
    assert "big_three" in interp
    assert "house_interpretation" in interp
    assert "rising_sign_interpretation" in interp
    assert "chart_shape" in interp
    assert "modality_element_distribution" in interp
    assert "retrograde_planets" in interp
    assert "retrograde_interpretations" in interp


@pytest.mark.asyncio
async def test_interpretations_have_source_and_placeholder_metadata():
    """Client can identify data source and placeholders via sources and placeholder_keys."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    interp = data.get("interpretations", {})
    assert "sources" in interp, "sources required for client to identify data provenance"
    assert "placeholder_keys" in interp, "placeholder_keys required to flag fill-in gaps"

    sources = interp.get("sources", {})
    placeholder_keys = interp.get("placeholder_keys", [])

    # Every planet_in_sign key should have a source (aspects: chart.aspects[].source, planet_in_house: per_house)
    for key in list(interp.get("planet_in_sign", {}).keys()):
        assert key in sources, f"planet_in_sign key {key} should have sources entry"
        assert sources[key] in ("database", "default")

    # Placeholder keys: planet_in_sign only (aspects use chart.aspects[].is_placeholder)
    for key in placeholder_keys:
        val = interp.get("planet_in_sign", {}).get(key)
        if val:
            assert is_placeholder_text(val), f"placeholder_keys[{key}] should match placeholder pattern"


@pytest.mark.asyncio
async def test_big_three_structure_and_metadata():
    """Big Three has correct shape; when present, includes source and is_placeholder."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    bt = data.get("interpretations", {}).get("big_three", {})
    # Structure: sun, moon, ascendant (each optional)
    for lum in ("sun", "moon", "ascendant"):
        if bt.get(lum):
            obj = bt[lum]
            assert "sign" in obj
            assert "source" in obj, f"big_three.{lum} should have source for client"
            assert "is_placeholder" in obj, f"big_three.{lum} should have is_placeholder"
            if obj.get("source"):
                assert obj["source"] == "database"


@pytest.mark.asyncio
async def test_aspects_have_type_and_interpretation_metadata():
    """Each aspect in chart has type, interpretation, source, is_placeholder."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    aspects = data.get("aspects", [])
    for a in aspects:
        assert "planet1" in a and "planet2" in a and "aspect" in a
        assert "type" in a, "aspect should have type (conjunction/stressful/easy-flowing)"
        assert "interpretation" in a or a.get("interpretation") is None
        assert "source" in a, "aspect should have source for client"
        assert "is_placeholder" in a, "aspect should have is_placeholder"


@pytest.mark.asyncio
async def test_house_interpretation_structure():
    """house_interpretation has per_house, shape, quadrant, hemisphere."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    hi = data.get("interpretations", {}).get("house_interpretation", {})
    assert "per_house" in hi
    assert "shape" in hi
    assert "quadrant" in hi
    assert "hemisphere" in hi

    per_house = hi.get("per_house", [])
    assert len(per_house) == 12
    for ph in per_house:
        assert "house" in ph
        assert "sign_on_cusp" in ph
        assert "planets" in ph
        assert "planet_interpretations" in ph
        assert "sign_interpretation" in ph


def test_is_placeholder_text_detects_known_patterns():
    """data_quality.is_placeholder_text correctly identifies placeholder content."""
    assert is_placeholder_text("[Add interpretation]")
    assert is_placeholder_text("[Add your interpretation here]")
    assert is_placeholder_text("[Add interpretation for Conjunction aspects]")
    assert is_placeholder_text("Venus in Pisces: [Add your interpretation here]")
    assert not is_placeholder_text("Bold, pioneering, and independent.")
    assert not is_placeholder_text(None)
    assert not is_placeholder_text("")
