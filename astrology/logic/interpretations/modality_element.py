"""
Detect modality and element distribution keys for interpretation lookup.
Based on planetary placements: which signs (by quality/element) have planets.
"""


def detect_modality_element_keys(
    by_quality: dict[str, int],
    by_element: dict[str, int],
) -> list[str]:
    """
    Determine which modality/element distribution keys apply from counts.

    by_quality: {"cardinal": n, "fixed": n, "mutable": n}
    by_element: {"fire": n, "earth": n, "air": n, "water": n}

    Returns keys like: element_fire_dominant, quality_cardinal_balanced, element_lacking_earth
    """
    keys: list[str] = []

    # Element: dominant (one has the most), balanced, or lacking
    if by_element:
        max_el = max(by_element.values())
        dominant = [k for k, v in by_element.items() if v == max_el]
        if len(dominant) == 1 and max_el > 0:
            keys.append(f"element_{dominant[0]}_dominant")
        elif max_el > 0:
            keys.append("element_balanced")
        for elem in ("fire", "earth", "air", "water"):
            if by_element.get(elem, 0) == 0:
                keys.append(f"element_lacking_{elem}")

    # Quality: dominant or balanced
    if by_quality:
        max_q = max(by_quality.values())
        dominant = [k for k, v in by_quality.items() if v == max_q]
        if len(dominant) == 1 and max_q > 0:
            keys.append(f"quality_{dominant[0]}_dominant")
        elif max_q > 0:
            keys.append("quality_balanced")

    return keys
