"""
Built-in generic interpretations for Sun, Moon, Rising, planets in houses, and aspects.
Used when the database has no interpretations (e.g., before seeding).
DB interpretations take precedence when present.
"""
# --- Signs (Sun, Moon, Rising) ---
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SUN_IN_SIGN = {
    "Sun in Aries": "Bold, pioneering, and independent. Natural leaders who thrive on initiative and new beginnings.",
    "Sun in Taurus": "Grounded, patient, and sensual. Values stability, comfort, and the physical world.",
    "Sun in Gemini": "Curious, adaptable, and communicative. Loves learning, connecting ideas, and variety.",
    "Sun in Cancer": "Nurturing, intuitive, and protective. Deep emotional roots and a strong connection to home.",
    "Sun in Leo": "Creative, generous, and confident. Natural performers who radiate warmth and seek recognition.",
    "Sun in Virgo": "Practical, analytical, and service-oriented. Strives for perfection and finds purpose in helpfulness.",
    "Sun in Libra": "Diplomatic, aesthetic, and relationship-focused. Seeks balance, harmony, and partnership.",
    "Sun in Scorpio": "Intense, perceptive, and transformative. Depth, passion, and a drive to uncover truth.",
    "Sun in Sagittarius": "Philosophical, adventurous, and optimistic. Seeks meaning, freedom, and broader horizons.",
    "Sun in Capricorn": "Ambitious, disciplined, and responsible. Builds lasting structures and values achievement.",
    "Sun in Aquarius": "Innovative, humanitarian, and independent. Forward-thinking with a concern for the collective.",
    "Sun in Pisces": "Compassionate, imaginative, and empathetic. Blends boundaries and connects to the transcendent.",
}

MOON_IN_SIGN = {
    "Moon in Aries": "Emotionally direct and impulsive. Needs action and independence to feel secure.",
    "Moon in Taurus": "Steady, comfort-seeking emotions. Security through stability and sensory pleasures.",
    "Moon in Gemini": "Versatile feelings that need expression. Emotional security through communication and variety.",
    "Moon in Cancer": "Deeply sensitive and protective. Strong need for emotional safety and nurturing connections.",
    "Moon in Leo": "Warm, proud emotions. Needs appreciation, loyalty, and creative expression.",
    "Moon in Virgo": "Practical, discerning feelings. Seeks order, usefulness, and tangible care.",
    "Moon in Libra": "Emotionally diplomatic and relationship-oriented. Needs harmony and partnership.",
    "Moon in Scorpio": "Intense, penetrating emotions. Seeks depth, loyalty, and transformative bonds.",
    "Moon in Sagittarius": "Optimistic, freedom-loving feelings. Needs meaning, adventure, and philosophical space.",
    "Moon in Capricorn": "Reserved, responsible emotions. Security through achievement and respect.",
    "Moon in Aquarius": "Detached, unconventional feelings. Needs friendship, ideals, and emotional freedom.",
    "Moon in Pisces": "Fluid, compassionate emotions. Blends with others and seeks spiritual connection.",
}

RISING_IN_SIGN = {
    "Rising in Aries": "Bold first impression. Projects confidence, initiative, and a direct, energetic approach to life.",
    "Rising in Taurus": "Steady, grounded presence. Appears calm, patient, and attuned to comfort and beauty.",
    "Rising in Gemini": "Quick, curious demeanor. Comes across as sociable, articulate, and adaptable.",
    "Rising in Cancer": "Gentle, protective impression. Presents as nurturing, intuitive, and somewhat reserved.",
    "Rising in Leo": "Warm, confident appearance. Projects charisma, pride, and a natural desire to shine.",
    "Rising in Virgo": "Refined, practical presence. Appears thoughtful, helpful, and attuned to details.",
    "Rising in Libra": "Charming, diplomatic impression. Projects grace, sociability, and a desire for harmony.",
    "Rising in Scorpio": "Intense, magnetic presence. Appears penetrating, private, and quietly powerful.",
    "Rising in Sagittarius": "Open, optimistic demeanor. Comes across as adventurous, philosophical, and free-spirited.",
    "Rising in Capricorn": "Serious, capable impression. Projects discipline, ambition, and quiet authority.",
    "Rising in Aquarius": "Unconventional, friendly presence. Appears inventive, detached, and socially aware.",
    "Rising in Pisces": "Soft, impressionable demeanor. Projects sensitivity, imagination, and a dreamy quality.",
}


def get_default_planet_in_sign(sun_sign: str, moon_sign: str, rising_sign: str) -> dict[str, str]:
    """Return built-in interpretations for Sun, Moon, and Rising in their signs."""
    result = {}
    if sun_sign and f"Sun in {sun_sign}" in SUN_IN_SIGN:
        result[f"Sun in {sun_sign}"] = SUN_IN_SIGN[f"Sun in {sun_sign}"]
    if moon_sign and f"Moon in {moon_sign}" in MOON_IN_SIGN:
        result[f"Moon in {moon_sign}"] = MOON_IN_SIGN[f"Moon in {moon_sign}"]
    if rising_sign and f"Rising in {rising_sign}" in RISING_IN_SIGN:
        result[f"Rising in {rising_sign}"] = RISING_IN_SIGN[f"Rising in {rising_sign}"]
    return result


# --- Planets in Houses ---
# Generic interpretations: planet energy expressed through the house's life area.
# Key format: "Planet in House N"
def _planet_in_house_defaults() -> dict[str, str]:
    d: dict[str, str] = {}
    planets = [
        ("Sun", "identity, vitality, self-expression"),
        ("Moon", "emotions, instincts, nurturing"),
        ("Mercury", "thinking, communication, learning"),
        ("Venus", "love, beauty, values"),
        ("Mars", "action, drive, assertion"),
        ("Jupiter", "expansion, faith, opportunity"),
        ("Saturn", "structure, responsibility, discipline"),
        ("Uranus", "innovation, rebellion, awakening"),
        ("Neptune", "imagination, spirituality, dissolution"),
        ("Pluto", "transformation, power, depth"),
        ("Chiron", "wounding, healing, teaching"),
    ]
    houses = [
        (1, "self, identity, and physical presence"),
        (2, "resources, values, and possessions"),
        (3, "communication, siblings, and local environment"),
        (4, "home, family, and inner foundation"),
        (5, "creativity, romance, and self-expression"),
        (6, "health, service, and daily routines"),
        (7, "partnership, marriage, and open relationships"),
        (8, "shared resources, transformation, and the unseen"),
        (9, "philosophy, travel, and higher meaning"),
        (10, "career, reputation, and public role"),
        (11, "friends, hopes, and group belonging"),
        (12, "subconscious, solitude, and release"),
    ]
    for pname, ptheme in planets:
        for hnum, htheme in houses:
            d[f"{pname} in House {hnum}"] = (
                f"{ptheme.capitalize()} expressed through {htheme}."
            )
    return d


PLANET_IN_HOUSE = _planet_in_house_defaults()


# --- Aspects (generic by type) ---
ASPECT_DEFAULTS = {
    "Conjunction": "Planets merge their energies; themes reinforce and blend. Intensity depends on the planets involved.",
    "Opposition": "Dynamic tension between two poles. Integration or awareness of both sides brings growth.",
    "Square": "Friction and challenge that can drive action. Often requires effort to harness constructively.",
    "Trine": "Ease and flow between energies. Natural talent or harmony in the areas involved.",
    "Sextile": "Cooperative, supportive connection. Opportunities that arise with modest effort.",
    "Quincunx": "Subtle friction requiring adjustment. Themes that don't align easily but can integrate with awareness.",
}


def get_default_planet_in_house(planet_house_pairs: list[tuple[str, int]]) -> dict[str, str]:
    """Return built-in interpretations for each planet-house pair present in the chart."""
    result = {}
    for pname, hnum in planet_house_pairs:
        key = f"{pname} in House {hnum}"
        if key in PLANET_IN_HOUSE:
            result[key] = PLANET_IN_HOUSE[key]
    return result


def get_default_aspects(aspect_keys: list[str]) -> dict[str, str]:
    """Return built-in interpretations for aspects. Keys like 'Sun square Moon' map to generic aspect-type text."""
    result = {}
    aspect_by_name = {a.lower(): a for a in ASPECT_DEFAULTS}
    for key in aspect_keys:
        if key in result:
            continue
        # Key format: "planet1 aspect_type planet2" (e.g. "Sun square Moon")
        parts = key.split()
        if len(parts) >= 3:
            aspect_name = parts[1]
            if aspect_name.lower() in aspect_by_name:
                canonical = aspect_by_name[aspect_name.lower()]
                result[key] = ASPECT_DEFAULTS[canonical]
    return result
