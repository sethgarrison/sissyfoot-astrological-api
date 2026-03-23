"""
Sign adverbs and aspect keyphrases for interpretations_summary.

Defaults are defined here and seeded into the database; runtime reads merged DB + defaults
via fetch_chart_lexicon_data in interpretations.lookup.
"""

from __future__ import annotations

# Shipped defaults (also written by seed_from_csv when DB cells are empty)
DEFAULT_SIGN_ADVERBS: dict[str, str] = {
    "Aries": "urgently",
    "Taurus": "realistically",
    "Gemini": "intelligently",
    "Cancer": "carefully",
    "Leo": "proudly",
    "Virgo": "precisely",
    "Libra": "adaptively",
    "Scorpio": "intensely",
    "Sagittarius": "far-reachingly",
    "Capricorn": "usefully",
    "Aquarius": "knowingly",
    "Pisces": "sympathetically",
}

# Normalized aspect name -> keyphrase. Conjunction omitted (handled in code).
DEFAULT_ASPECT_KEYPHRASES_NORM: dict[str, str] = {
    "sextile": "combines pleasantly with",
    "square": "interacts stressfully with",
    "trine": "combines very easily with",
    "opposition": "faces and challenges",
    "semisextile": "combines somewhat easily with",
    "semisquare": "interacts somewhat stressfully with",
    "sesquisquare": "interacts somewhat stressfully with",
    "quincunx": "interacts awkwardly with",
}

# Back-compat alias
SIGN_ADVERBS = DEFAULT_SIGN_ADVERBS


def normalize_aspect_name_for_lexicon(aspect: str) -> str:
    if not aspect:
        return ""
    return aspect.strip().lower().replace("-", "").replace(" ", "")


def is_conjunction_aspect(aspect: str) -> bool:
    return normalize_aspect_name_for_lexicon(aspect) == "conjunction"


def sign_adverb(sign: str, sign_adverbs: dict[str, str]) -> str:
    if not sign:
        return ""
    return (sign_adverbs.get(sign) or "").strip()


def aspect_keyphrase(aspect: str, aspect_keyphrase_by_norm: dict[str, str]) -> str | None:
    """
    Return keyphrase for an aspect name, or None for conjunction / unknown / empty override.
    aspect_keyphrase_by_norm: normalized name -> phrase (empty string means explicitly no phrase).
    """
    norm = normalize_aspect_name_for_lexicon(aspect)
    if norm == "conjunction":
        return None
    phrase = aspect_keyphrase_by_norm.get(norm)
    if phrase is None:
        return None
    stripped = phrase.strip()
    return stripped if stripped else None


def placement_synthesis(
    planet_keyword: str | None,
    sign: str,
    sign_adverbs: dict[str, str],
) -> str:
    """{planet_keyword} {sign_adverb} — no house keyword in the string."""
    pkw = (planet_keyword or "").strip()
    adv = sign_adverb(sign, sign_adverbs)
    parts = [x for x in (pkw, adv) if x]
    return " ".join(parts)
