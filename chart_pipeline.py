"""
Chart computation and assembly of ChartAPIResponse (chart_data + interpretation).
Keeps ephemeris logic and DB enrichment out of main.py.
"""

from __future__ import annotations

import os
from typing import Optional

from kerykeion import AstrologicalSubject
from kerykeion.aspects import AspectsFactory
from sqlalchemy.ext.asyncio import AsyncSession

from interpretations.data_quality import is_placeholder_text
from interpretations.defaults import (
    get_default_planet_in_house,
    get_default_planet_in_sign,
    get_default_aspects,
)
from interpretations.lexicons import DEFAULT_ASPECT_KEYPHRASES_NORM, DEFAULT_SIGN_ADVERBS
from interpretations.lookup import fetch_chart_lexicon_data, fetch_interpretations
from interpretations.chart_shapes import detect_chart_shape, detect_distributions
from interpretations.modality_element import detect_modality_element_keys
from interpretations.summary import build_interpretations_summary
from schemas.chart_response import (
    AspectData,
    ChartAPIResponse,
    ChartCore,
    ChartData,
    ChartDataDistributionBucket,
    ChartInterpretation,
    ChartInterpretationsBigThree,
    ChartInterpretationsShape,
    ContextInterpretation,
    ElementDistribution,
    ElementDistributionData,
    HouseCusp,
    HouseGroupInterpretationText,
    HouseInterpretation,
    KeyedInterpretation,
    LunarNodePosition,
    LunarPhaseData,
    MoonInterpretation,
    PlanetInterpretation,
    PlanetInterpretationText,
    PlanetPosition,
    QualityDistribution,
    QualityDistributionData,
    RisingInterpretation,
    SignPlacementOverview,
    SunInterpretation,
    AspectInterpretation as ClientAspectInterpretation,
)

SIGN_FULL = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces",
}

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

HOUSE_SYSTEMS = {"whole_sign": "W", "placidus": "P", "WSH": "W"}
DEFAULT_HOUSE_SYSTEM = "whole_sign"

NODE_NAMES = {"True_North_Lunar_Node", "True_South_Lunar_Node", "North_Node", "South_Node"}


def _sign(abbr: str) -> str:
    return SIGN_FULL.get(abbr, abbr)


def _house_num(house_str: str) -> int:
    return HOUSE_NUM.get(house_str, 0)


def compute_sign_placement_overview(planets: list[PlanetPosition]) -> SignPlacementOverview:
    signs_with_planets: dict[str, list[str]] = {}
    by_quality: dict[str, list[str]] = {"cardinal": [], "fixed": [], "mutable": []}
    by_element: dict[str, list[str]] = {"fire": [], "earth": [], "air": [], "water": []}
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


def build_chart_core(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    *,
    city: Optional[str] = None,
    nation: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    tz_str: Optional[str] = None,
    name: str = "",
    house_system: str = DEFAULT_HOUSE_SYSTEM,
) -> ChartCore:
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
        houses.append(
            HouseCusp(
                number=i,
                sign=_sign(h.sign),
                degree=round(h.position, 4),
                abs_degree=round(h.abs_pos, 4),
            )
        )

    aspects: list[AspectData] = []
    try:
        asp_result = AspectsFactory.natal_aspects(subject._model)
        for a in asp_result.aspects:
            if a.p1_name in NODE_NAMES or a.p2_name in NODE_NAMES:
                continue
            aspects.append(
                AspectData(
                    planet1=a.p1_name.replace("_", " "),
                    planet2=a.p2_name.replace("_", " "),
                    aspect=a.aspect,
                    aspect_degrees=a.aspect_degrees,
                    orbit=round(a.orbit, 4),
                    movement=a.aspect_movement or "",
                )
            )
    except Exception:
        pass

    lp = subject._model.lunar_phase
    lunar_phase = LunarPhaseData(
        degrees_between=round(lp.degrees_between_s_m, 4),
        phase_name=lp.moon_phase_name,
        emoji=lp.moon_emoji,
    )

    return ChartCore(
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
        houses_overview=compute_sign_placement_overview(planets),
        aspects=aspects,
    )


def _quality_bucket_interpretation(q: str, mod: dict[str, str]) -> Optional[str]:
    k = f"quality_{q}_dominant"
    if k in mod:
        return mod[k]
    if "quality_balanced" in mod:
        return mod["quality_balanced"]
    return None


def _element_bucket_interpretation(elem: str, mod: dict[str, str]) -> Optional[str]:
    k = f"element_{elem}_dominant"
    if k in mod:
        return mod[k]
    if "element_balanced" in mod:
        return mod["element_balanced"]
    lk = f"element_lacking_{elem}"
    if lk in mod:
        return mod[lk]
    return None


def _chart_data_from_core(core: ChartCore, modality_interp: dict[str, str]) -> ChartData:
    o = core.houses_overview
    bq = o.by_quality
    be = o.by_element

    def qb(q: str) -> ChartDataDistributionBucket:
        d = bq[q]
        return ChartDataDistributionBucket(
            count=d.count,
            signs=list(d.signs),
            planets=list(d.planets),
            interpretation=_quality_bucket_interpretation(q, modality_interp),
        )

    def eb(e: str) -> ChartDataDistributionBucket:
        d = be[e]
        return ChartDataDistributionBucket(
            count=d.count,
            signs=list(d.signs),
            planets=list(d.planets),
            interpretation=_element_bucket_interpretation(e, modality_interp),
        )

    return ChartData(
        aspects=list(core.aspects),
        planets=list(core.planets),
        lunar_nodes=list(core.lunar_nodes),
        houses=list(core.houses),
        by_quality=QualityDistributionData(cardinal=qb("cardinal"), fixed=qb("fixed"), mutable=qb("mutable")),
        by_element=ElementDistributionData(fire=eb("fire"), earth=eb("earth"), air=eb("air"), water=eb("water")),
        lunar_phase=core.lunar_phase,
    )


def _spatial_keyed(dist: dict[str, str]) -> KeyedInterpretation:
    if not dist:
        return KeyedInterpretation()
    keys = sorted(dist.keys())
    return KeyedInterpretation(
        key="|".join(keys),
        interpretation="\n\n".join(dist[k] for k in keys),
    )


def _quality_context(mod: dict[str, str]) -> KeyedInterpretation:
    order = (
        "quality_cardinal_dominant",
        "quality_fixed_dominant",
        "quality_mutable_dominant",
        "quality_balanced",
    )
    for k in order:
        if k in mod:
            return KeyedInterpretation(key=k, interpretation=mod[k])
    for k in sorted(mod.keys()):
        if k.startswith("quality_"):
            return KeyedInterpretation(key=k, interpretation=mod[k])
    return KeyedInterpretation()


def _modality_element_context(mod: dict[str, str]) -> KeyedInterpretation:
    for k in sorted(mod.keys()):
        if k.startswith("element_"):
            return KeyedInterpretation(key=k, interpretation=mod[k])
    return KeyedInterpretation()


def _big_three_from_bt(
    bt: dict,
    sun_sign: str,
    moon_sign: str,
    rising_sign: str,
) -> ChartInterpretationsBigThree:
    sd = bt.get("sun") or {}
    md = bt.get("moon") or {}
    ad = bt.get("ascendant") or {}
    return ChartInterpretationsBigThree(
        sun=SunInterpretation(
            sign=str(sd.get("sign") or sun_sign),
            archetypes_balanced=str(sd.get("archetypes_balanced") or ""),
            archetypes_unbalanced=str(sd.get("archetypes_unbalanced") or ""),
            journey=str(sd.get("journey") or ""),
            gifts=str(sd.get("gifts") or ""),
            challenges=str(sd.get("challenges") or ""),
            interpretation=str(sd.get("interpretation") or sd.get("sign_interpretation") or ""),
        ),
        moon=MoonInterpretation(
            sign=str(md.get("sign") or moon_sign),
            nature=str(md.get("nature") or ""),
            sources_of_contentment=str(md.get("sources_of_contentment") or ""),
            keywords=md.get("keywords"),
            interpretation=str(md.get("interpretation") or ""),
        ),
        ascendant=RisingInterpretation(
            sign=str(ad.get("sign") or rising_sign),
            impression=str(ad.get("impression") or ""),
            appearance=str(ad.get("appearance") or ""),
            childhood=str(ad.get("childhood") or ""),
            balance=str(ad.get("balance") or ""),
            interpretation=str(ad.get("interpretation") or ""),
        ),
    )


def _house_groups_from_summary(
    summary,
    house_sign_interp: dict,
) -> list[HouseInterpretation]:
    out: list[HouseInterpretation] = []
    for hg in summary.house_groups:
        house_in = ""
        key = (hg.house, hg.sign_on_cusp)
        if key in house_sign_interp:
            house_in = house_sign_interp[key] or ""
        elif hg.house == 1 and isinstance(house_sign_interp.get("rising"), str):
            house_in = house_sign_interp["rising"]
        planets: list[PlanetInterpretation] = []
        for pl in hg.placements:
            long = pl.long
            pit = PlanetInterpretationText(
                planet_in_sign=(long.in_sign if long else None) or "",
                planet_in_house=(long.in_house if long else None) or "",
            )
            aspects = [
                ClientAspectInterpretation(
                    aspect=a.aspect,
                    aspect_type=a.aspect_type,
                    aspect_keyphrase=a.aspect_keyphrase,
                    other_body=a.other_body,
                    other_sign=a.other_sign,
                    other_planet_keyword=a.other_planet_keyword,
                    other_sign_adverb=a.other_sign_adverb,
                    synthesis=a.synthesis,
                    interpretation=a.interpretation,
                    is_placeholder=a.is_placeholder,
                )
                for a in pl.aspects
            ]
            planets.append(
                PlanetInterpretation(
                    body=pl.body,
                    sign=pl.sign,
                    sign_adverb=pl.sign_adverb,
                    planet_keyword=pl.planet_keyword or "",
                    synthesis=pl.synthesis,
                    retrograde=pl.retrograde,
                    aspects=aspects,
                    interpretation=pit,
                )
            )
        out.append(
            HouseInterpretation(
                house=hg.house,
                house_keyword=hg.house_keyword or "",
                sign_on_cusp=hg.sign_on_cusp,
                interpretation=HouseGroupInterpretationText(house_in_sign=house_in),
                planets=planets,
            )
        )
    return out


async def build_chart_api_response(core: ChartCore, session: AsyncSession) -> ChartAPIResponse:
    planet_sign_pairs = [(p.name, p.sign) for p in core.planets]
    planet_house_pairs = [(p.name, p.house) for p in core.planets]
    aspect_keys = [f"{a.planet1} {a.aspect} {a.planet2}" for a in core.aspects]
    planet_dicts = [{"name": p.name, "abs_degree": p.abs_degree, "house": p.house} for p in core.planets]
    chart_shape = detect_chart_shape(planet_dicts)
    distribution_keys = detect_distributions(planet_dicts)
    by_quality = {k: v.count for k, v in core.houses_overview.by_quality.items()}
    by_element = {k: v.count for k, v in core.houses_overview.by_element.items()}
    modality_element_keys = detect_modality_element_keys(by_quality, by_element)
    retrograde_planets = {p.name for p in core.planets if p.retrograde}

    try:
        house_cusps = [(h.number, h.sign) for h in core.houses]
        interp = await fetch_interpretations(
            session,
            planet_sign_pairs=planet_sign_pairs,
            planet_house_pairs=planet_house_pairs,
            aspect_keys=aspect_keys,
            chart_shape=chart_shape,
            distribution_keys=distribution_keys,
            modality_element_keys=modality_element_keys,
            retrograde_planets=retrograde_planets,
            rising_sign=core.rising_sign,
            sun_sign=core.sun_sign,
            moon_sign=core.moon_sign,
            house_cusps=house_cusps,
        )
        planet_in_sign = dict(interp["planet_in_sign"])
    except Exception:
        planet_in_sign = {}
        interp = {
            "planet_in_house": {},
            "aspects": {},
            "aspects_detail": {},
            "big_three": {"sun": None, "moon": None, "ascendant": None},
            "house_sign_interpretations": {},
            "rising_sign_interpretation": None,
            "chart_shape": {"primary": chart_shape, "interpretation": None, "distribution": {}},
            "modality_element_distribution": {},
            "retrograde_planets": sorted(retrograde_planets),
            "retrograde_interpretations": {},
        }

    planet_in_house = dict(interp.get("planet_in_house", {}))
    aspects_interp = dict(interp.get("aspects", {}))

    for key, text in get_default_planet_in_sign(core.sun_sign, core.moon_sign, core.rising_sign).items():
        if key not in planet_in_sign:
            planet_in_sign[key] = text
    for key, text in get_default_planet_in_house(planet_house_pairs).items():
        if key not in planet_in_house:
            planet_in_house[key] = text
    for key, text in get_default_aspects(aspect_keys).items():
        if key not in aspects_interp:
            aspects_interp[key] = text

    aspects_detail = interp.get("aspects_detail", {})
    for a in core.aspects:
        key = f"{a.planet1} {a.aspect} {a.planet2}"
        detail = aspects_detail.get(key, {})
        a.type = detail.get("type")
        interp_text = detail.get("interpretation") or aspects_interp.get(key)
        a.interpretation = interp_text
        a.source = (
            "database"
            if key in interp.get("aspects", {})
            else ("default" if key in aspects_interp else None)
        )
        a.is_placeholder = is_placeholder_text(interp_text) if interp_text else False

    modality_interp = dict(interp.get("modality_element_distribution") or {})
    chart_data = _chart_data_from_core(core, modality_interp)

    cs = interp.get("chart_shape", {}) or {}
    dist = cs.get("distribution") or {}

    context = ContextInterpretation(
        shape=ChartInterpretationsShape(
            key=str(cs.get("primary") or ""),
            interpretation=str(cs.get("interpretation") or ""),
        ),
        spatial_distribution=_spatial_keyed(dist),
        quality_distribution=_quality_context(modality_interp),
        modality_distribution=_modality_element_context(modality_interp),
    )

    bt = interp.get("big_three", {})
    big_three = _big_three_from_bt(bt, core.sun_sign, core.moon_sign, core.rising_sign)

    try:
        planet_kw, house_kw, sign_adv, asp_norm = await fetch_chart_lexicon_data(session)
    except Exception:
        planet_kw, house_kw = {}, {}
        sign_adv = dict(DEFAULT_SIGN_ADVERBS)
        asp_norm = dict(DEFAULT_ASPECT_KEYPHRASES_NORM)

    summary = build_interpretations_summary(
        planets=core.planets,
        houses=core.houses,
        aspects=core.aspects,
        planet_in_sign=planet_in_sign,
        planet_in_house=planet_in_house,
        planet_keywords=planet_kw,
        house_keywords=house_kw,
        sign_adverbs=sign_adv,
        aspect_keyphrase_by_norm=asp_norm,
        chart_shape_primary=cs.get("primary"),
        chart_shape_interpretation=cs.get("interpretation"),
        distribution=dist,
        modality_element_distribution=modality_interp,
        big_three_dict=big_three.model_dump(),
    )

    house_sign_interp = dict(interp.get("house_sign_interpretations", {}))
    house_sign_interp["rising"] = interp.get("rising_sign_interpretation")
    house_groups = _house_groups_from_summary(summary, house_sign_interp)

    interpretation = ChartInterpretation(
        big_three=big_three,
        context=context,
        house_groups=house_groups,
        retrograde_planets=list(interp.get("retrograde_planets", [])),
        retrograde_interpretations=interp.get("retrograde_interpretations", {}),
    )

    return ChartAPIResponse(
        name=core.name or "",
        birth_datetime=core.birth_datetime,
        latitude=core.latitude,
        longitude=core.longitude,
        house_system=core.house_system,
        sun_sign=core.sun_sign,
        moon_sign=core.moon_sign,
        rising_sign=core.rising_sign,
        chart_data=chart_data,
        interpretation=interpretation,
    )
