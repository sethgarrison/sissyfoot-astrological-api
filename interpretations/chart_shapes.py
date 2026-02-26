"""
Chart shape and distribution detection based on Marc Edmund Jones patterns.
Uses the 10 traditional planets (excludes Chiron and Nodes) for shape detection.
"""
from typing import Optional


# Planets to include for chart shape (per Jones: Sun through Pluto)
SHAPE_PLANETS = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}

# House groupings
HEMISPHERE_NORTHERN = {7, 8, 9, 10, 11, 12}  # above horizon
HEMISPHERE_SOUTHERN = {1, 2, 3, 4, 5, 6}     # below horizon
HEMISPHERE_EASTERN = {10, 11, 12, 1, 2, 3}   # ascendant side
HEMISPHERE_WESTERN = {4, 5, 6, 7, 8, 9}      # descendant side
QUADRANT_1 = {1, 2, 3}
QUADRANT_2 = {4, 5, 6}
QUADRANT_3 = {7, 8, 9}
QUADRANT_4 = {10, 11, 12}


def _normalize_angle(deg: float) -> float:
    """Normalize to 0-360."""
    return ((deg % 360) + 360) % 360


def _angular_distance(a: float, b: float) -> float:
    """Shortest angular distance between two positions (0-180)."""
    d = abs((a % 360) - (b % 360))
    return min(d, 360 - d)


def _span(longitudes: list[float]) -> float:
    """Span of longitudes (handling 0/360 wrap). Span = 360 - largest_gap."""
    if len(longitudes) < 2:
        return 0.0
    largest_gap = _largest_gap(longitudes)
    return 360 - largest_gap


def _largest_gap(longitudes: list[float]) -> float:
    """Largest gap between consecutive (sorted) longitudes."""
    if len(longitudes) < 2:
        return 360.0
    lons = sorted(longitudes)
    gaps = []
    for i in range(len(lons)):
        next_i = (i + 1) % len(lons)
        gap = (lons[next_i] - lons[i]) % 360
        if gap < 0:
            gap += 360
        gaps.append(gap)
    return max(gaps)


def _count_handle(longitudes: list[float]) -> int:
    """Count planets in the 'handle' - the smaller group opposite the main cluster."""
    if len(longitudes) < 3:
        return 0
    lons = sorted(longitudes)
    largest_gap = 0
    gap_index = -1
    for i in range(len(lons)):
        next_i = (i + 1) % len(lons)
        gap = (lons[next_i] - lons[i]) % 360
        if gap < 0:
            gap += 360
        if gap > largest_gap:
            largest_gap = gap
            gap_index = i
    if gap_index < 0 or largest_gap < 100:
        return 0
    # The "handle" is the smaller of the two groups split by the largest gap
    count_after = (len(lons) - gap_index - 1) % len(lons)
    if count_after == 0:
        count_after = len(lons)
    count_before = len(lons) - count_after
    return min(count_before, count_after)


def _count_clumps(longitudes: list[float], gap_threshold: float = 60) -> int:
    """Count groupings: consecutive planets within gap_threshold form a clump."""
    if len(longitudes) < 2:
        return len(longitudes)
    lons = sorted(longitudes)
    clumps = 1
    for i in range(len(lons)):
        next_i = (i + 1) % len(lons)
        gap = (lons[next_i] - lons[i]) % 360
        if gap < 0:
            gap += 360
        if gap > gap_threshold:
            clumps += 1
    return clumps


def _is_seesaw(longitudes: list[float]) -> bool:
    """Two groups roughly opposite each other with empty space on both sides."""
    if len(longitudes) < 4:
        return False
    lons = sorted(longitudes)
    largest_gap = _largest_gap(lons)
    # For seesaw, largest gap should be ~120-180 (empty third to half)
    if largest_gap < 100 or largest_gap > 200:
        return False
    # Two groups - check they're roughly opposite
    gap_idx = 0
    for i in range(len(lons)):
        next_i = (i + 1) % len(lons)
        gap = (lons[next_i] - lons[i]) % 360
        if gap > 150:
            gap_idx = i
            break
    # Split into two groups
    group1 = lons[: gap_idx + 1]
    group2 = lons[gap_idx + 1 :]
    if len(group1) < 2 or len(group2) < 2:
        return False
    # Centers should be roughly 180 apart
    c1 = sum(group1) / len(group1)
    c2 = sum(group2) / len(group2)
    diff = abs((c1 - c2 + 180) % 360 - 180)
    return diff < 60


def detect_chart_shape(planets: list[dict]) -> Optional[str]:
    """
    Detect chart shape from planet positions.
    planets: list of {"name": str, "abs_degree": float, "house": int}
    Returns: splash | splay | bundle | bowl | locomotive | bucket | see_saw
    """
    # Filter to 10 traditional planets, get longitudes
    lons = [
        p["abs_degree"]
        for p in planets
        if p.get("name") in SHAPE_PLANETS
    ]
    if len(lons) < 3:
        return None

    span = _span(lons)
    largest_gap = _largest_gap(lons)
    handle_count = _count_handle(lons)
    clumps = _count_clumps(lons)

    # Bucket: bowl + 1-2 planets in the "handle" (opposite the main group)
    if handle_count in (1, 2) and span <= 180 and len(lons) >= 5:
        return "bucket"

    # Bundle: within 120°
    if span <= 120:
        return "bundle"

    # Bowl: 120° < span <= 180°
    if 120 < span <= 180:
        return "bowl"

    # See-Saw: two opposing groups
    if _is_seesaw(lons):
        return "see_saw"

    # Locomotive: span ~240°, one trine empty
    if 200 <= span <= 280 and largest_gap >= 80:
        return "locomotive"

    # Splay: 3+ clumps of 3+ planets (irregular)
    if clumps >= 3:
        return "splay"

    # Splash: evenly distributed (span large, no huge gaps)
    if span >= 200 and largest_gap < 80:
        return "splash"

    # Default to splay for irregular
    return "splay"


def detect_distributions(planets: list[dict]) -> list[str]:
    """
    Detect hemisphere/quadrant emphases.
    planets: list of {"name": str, "house": int}
    Returns list of distribution keys that apply (e.g. hemisphere_northern, quadrant_4).
    """
    houses = [p["house"] for p in planets if p.get("house") and 1 <= p["house"] <= 12]
    if not houses:
        return []

    counts = {
        "hemisphere_northern": sum(1 for h in houses if h in HEMISPHERE_NORTHERN),
        "hemisphere_southern": sum(1 for h in houses if h in HEMISPHERE_SOUTHERN),
        "hemisphere_eastern": sum(1 for h in houses if h in HEMISPHERE_EASTERN),
        "hemisphere_western": sum(1 for h in houses if h in HEMISPHERE_WESTERN),
        "quadrant_1": sum(1 for h in houses if h in QUADRANT_1),
        "quadrant_2": sum(1 for h in houses if h in QUADRANT_2),
        "quadrant_3": sum(1 for h in houses if h in QUADRANT_3),
        "quadrant_4": sum(1 for h in houses if h in QUADRANT_4),
    }
    total = len(houses)
    # Consider it an "emphasis" if that region has more than half the planets
    threshold = total / 2
    return [k for k, v in counts.items() if v > threshold]
