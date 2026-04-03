"""
Test chart API wire shape: chart_data (drawing) + interpretation (readings).
Run: pytest astrology/tests/test_interpretations.py -v
Requires: database seeded (python -m astrology.scripts.seed, python -m astrology.scripts.seed_from_csv)
"""
import pytest
from httpx import ASGITransport, AsyncClient

from astrology.logic.interpretations.data_quality import is_placeholder_text
from main import app


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
async def test_chart_top_level_and_chart_data():
    """Response has chart_data for drawing (aspects, planets, distributions, lunar_phase)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    assert "chart_data" in data
    assert "interpretation" in data
    assert "interpretations" not in data
    assert "interpretations_summary" not in data

    cd = data["chart_data"]
    for key in (
        "aspects",
        "planets",
        "lunar_nodes",
        "houses",
        "by_quality",
        "by_element",
        "lunar_phase",
    ):
        assert key in cd

    bq = cd["by_quality"]
    for q in ("cardinal", "fixed", "mutable"):
        assert q in bq
        assert "count" in bq[q] and "signs" in bq[q] and "planets" in bq[q]

    be = cd["by_element"]
    for e in ("fire", "earth", "air", "water"):
        assert e in be


@pytest.mark.asyncio
async def test_interpretation_structure():
    """interpretation: big_three, context, house_groups, retrograde fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    interp = data["interpretation"]
    assert "big_three" in interp
    assert "context" in interp
    assert "house_groups" in interp
    assert "retrograde_planets" in interp
    assert "retrograde_interpretations" in interp

    ctx = interp["context"]
    assert "shape" in ctx
    assert "spatial_distribution" in ctx
    assert "quality_distribution" in ctx
    assert "modality_distribution" in ctx

    bt = interp["big_three"]
    for lum in ("sun", "moon", "ascendant"):
        assert lum in bt
        assert "sign" in bt[lum]


@pytest.mark.asyncio
async def test_house_groups_and_placements():
    """house_groups: house, sign_on_cusp, interpretation.house_in_sign, planets with aspects."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    groups = data["interpretation"]["house_groups"]
    assert len(groups) >= 1
    for hg in groups:
        assert "house" in hg
        assert "house_keyword" in hg
        assert "sign_on_cusp" in hg
        assert "interpretation" in hg
        assert "house_in_sign" in hg["interpretation"]
        assert "planets" in hg
        for pl in hg["planets"]:
            assert "body" in pl
            assert "sign" in pl
            assert "interpretation" in pl
            assert "planet_in_sign" in pl["interpretation"]
            assert "planet_in_house" in pl["interpretation"]
            assert "aspects" in pl
            for asp in pl["aspects"]:
                assert "aspect" in asp
                assert "other_body" in asp
                assert "synthesis" in asp


@pytest.mark.asyncio
async def test_aspects_in_chart_data_have_drawing_metadata():
    """Aspect rows live under chart_data; include type, interpretation, source, is_placeholder."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/chart", params=CHART_PARAMS)
        assert r.status_code == 200
        data = r.json()

    aspects = data["chart_data"]["aspects"]
    assert isinstance(aspects, list)
    assert len(aspects) > 0
    for a in aspects:
        assert "planet1" in a and "planet2" in a and "aspect" in a
        assert "type" in a
        assert "interpretation" in a or a.get("interpretation") is None
        assert "source" in a
        assert "is_placeholder" in a


def test_is_placeholder_text_detects_known_patterns():
    """data_quality.is_placeholder_text correctly identifies placeholder content."""
    assert is_placeholder_text("[Add interpretation]")
    assert is_placeholder_text("[Add your interpretation here]")
    assert is_placeholder_text("[Add interpretation for Conjunction aspects]")
    assert is_placeholder_text("Venus in Pisces: [Add your interpretation here]")
    assert not is_placeholder_text("Bold, pioneering, and independent.")
    assert not is_placeholder_text(None)
    assert not is_placeholder_text("")
