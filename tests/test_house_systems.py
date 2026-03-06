"""
Test Whole Sign vs Placidus house systems.
Run: python -m pytest tests/test_house_systems.py -v
   or: python tests/test_house_systems.py
"""
from main import build_chart

SIGN_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def test_whole_sign_cusps_at_zero():
    """Whole Sign: every house cusp must be at 0° of its sign."""
    chart = build_chart(
        1990, 6, 15, 12, 0,
        lat=40.7128, lng=-74.006, tz_str="America/New_York",
        house_system="whole_sign",
    )
    assert chart.house_system == "whole_sign"
    for h in chart.houses:
        assert h.degree == 0.0, f"House {h.number} ({h.sign}): expected 0°, got {h.degree}°"


def test_whole_sign_zodiac_order():
    """Whole Sign: houses follow zodiac order from rising sign."""
    chart = build_chart(
        1990, 6, 15, 12, 0,
        lat=40.7128, lng=-74.006, tz_str="America/New_York",
        house_system="whole_sign",
    )
    rising_idx = SIGN_ORDER.index(chart.rising_sign)
    expected = [SIGN_ORDER[(rising_idx + i) % 12] for i in range(12)]
    actual = [h.sign for h in chart.houses]
    assert actual == expected, f"Expected {expected}, got {actual}"


def test_placidus_cusps_vary():
    """Placidus: house cusps have varying degrees (not all 0°)."""
    chart = build_chart(
        1990, 6, 15, 12, 0,
        lat=40.7128, lng=-74.006, tz_str="America/New_York",
        house_system="placidus",
    )
    assert chart.house_system == "placidus"
    # At least one cusp should have a non-zero degree (ascendant degree)
    non_zero = [h for h in chart.houses if h.degree != 0.0]
    assert len(non_zero) > 0, "Placidus should have some cusps with non-zero degrees"


def test_house_systems_produce_different_placements():
    """WSH and Placidus can assign planets to different houses."""
    lat, lng, tz = 40.7128, -74.006, "America/New_York"
    wsh = build_chart(1990, 6, 15, 12, 0, lat=lat, lng=lng, tz_str=tz, house_system="whole_sign")
    plc = build_chart(1990, 6, 15, 12, 0, lat=lat, lng=lng, tz_str=tz, house_system="placidus")
    wsh_houses = {p.name: p.house for p in wsh.planets}
    plc_houses = {p.name: p.house for p in plc.planets}
    assert wsh_houses != plc_houses, "WSH and Placidus should differ for at least one planet"


def test_default_is_whole_sign():
    """Default house system should be whole_sign."""
    chart = build_chart(
        1990, 6, 15, 12, 0,
        lat=40.7128, lng=-74.006, tz_str="America/New_York",
    )
    assert chart.house_system == "whole_sign"
    assert chart.houses[0].degree == 0.0


if __name__ == "__main__":
    import subprocess
    subprocess.run(["python", "-m", "pytest", __file__, "-v"])
