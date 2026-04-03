"""Build internal house-grouped synthesis + aspects (consumed by chart_pipeline, not the wire JSON)."""

from __future__ import annotations

from .lexicons import (
    aspect_keyphrase,
    is_conjunction_aspect,
    placement_synthesis,
    sign_adverb,
)
from astrology.schema.interpretations_summary import (
    ChartContextSummary,
    ChartShapeSummary,
    HouseGroupSummary,
    InterpretationsSummary,
    PlacementLongTexts,
    SummaryAspectItem,
    SummaryPlacement,
)


def _planet_kw(planet_keywords: dict[str, str | None], name: str) -> str | None:
    v = planet_keywords.get(name)
    if v is not None:
        v = v.strip()
        return v if v else None
    return None


def build_interpretations_summary(
    *,
    planets: list,  # items with .name, .sign, .house, .retrograde
    houses: list,  # items with .number, .sign
    aspects: list,  # items with .planet1, .planet2, .aspect, .type, .interpretation, .is_placeholder
    planet_in_sign: dict[str, str],
    planet_in_house: dict[str, str],
    planet_keywords: dict[str, str | None],
    house_keywords: dict[int, str | None],
    sign_adverbs: dict[str, str],
    aspect_keyphrase_by_norm: dict[str, str],
    chart_shape_primary: str | None,
    chart_shape_interpretation: str | None,
    distribution: dict[str, str],
    modality_element_distribution: dict[str, str],
    big_three_dict: dict,
) -> InterpretationsSummary:
    by_name = {p.name: p for p in planets}
    house_cusp = {h.number: h.sign for h in houses}

    # Precompute placement synthesis per planet (for conjunction reuse)
    synthesis_by_planet: dict[str, str] = {}
    for p in planets:
        pkw = _planet_kw(planet_keywords, p.name)
        synthesis_by_planet[p.name] = placement_synthesis(pkw, p.sign, sign_adverbs)

    # Aspects involving each planet (same aspect may appear under both endpoints)
    aspects_by_planet: dict[str, list] = {p.name: [] for p in planets}
    for a in aspects:
        aspects_by_planet.setdefault(a.planet1, []).append(a)
        if a.planet2 != a.planet1:
            aspects_by_planet.setdefault(a.planet2, []).append(a)

    def aspect_summary_for(focal: str, a) -> SummaryAspectItem:
        other = a.planet2 if a.planet1 == focal else a.planet1
        other_p = by_name.get(other)
        other_sign = other_p.sign if other_p else ""
        okw = _planet_kw(planet_keywords, other)
        oadv = sign_adverb(other_sign, sign_adverbs)

        if is_conjunction_aspect(a.aspect):
            syn = synthesis_by_planet.get(
                other, placement_synthesis(okw, other_sign, sign_adverbs)
            )
            kp = None
        else:
            kp = aspect_keyphrase(a.aspect, aspect_keyphrase_by_norm)
            if kp:
                parts = [x for x in (kp, okw or "", oadv) if x]
                syn = " ".join(parts).strip()
            else:
                syn = ""

        return SummaryAspectItem(
            aspect=a.aspect,
            aspect_type=a.type,
            aspect_keyphrase=kp,
            other_body=other,
            other_sign=other_sign,
            other_planet_keyword=okw,
            other_sign_adverb=oadv or None,
            synthesis=syn,
            interpretation=a.interpretation,
            is_placeholder=bool(getattr(a, "is_placeholder", False)),
        )

    # Bucket planets by house
    by_house: dict[int, list] = {i: [] for i in range(1, 13)}
    for p in planets:
        h = p.house
        if 1 <= h <= 12:
            by_house[h].append(p)

    house_groups: list[HouseGroupSummary] = []
    for num in range(1, 13):
        plist = by_house[num]
        if not plist:
            continue
        hk = house_keywords.get(num)
        if hk is not None:
            hk = hk.strip() or None
        sign_on = house_cusp.get(num, "")
        placements: list[SummaryPlacement] = []
        for p in plist:
            pkw = _planet_kw(planet_keywords, p.name)
            adv = sign_adverb(p.sign, sign_adverbs)
            syn = synthesis_by_planet[p.name]
            sign_key = f"{p.name} in {p.sign}"
            house_key = f"{p.name} in House {p.house}"
            long_txt = PlacementLongTexts(
                in_sign=planet_in_sign.get(sign_key),
                in_house=planet_in_house.get(house_key),
            )
            if long_txt.in_sign is None and long_txt.in_house is None:
                long_txt = None
            asp_items = [
                aspect_summary_for(p.name, a)
                for a in aspects_by_planet.get(p.name, [])
            ]
            placements.append(
                SummaryPlacement(
                    body=p.name,
                    sign=p.sign,
                    sign_adverb=adv,
                    planet_keyword=pkw,
                    synthesis=syn,
                    retrograde=p.retrograde,
                    aspects=asp_items,
                    long=long_txt,
                )
            )
        house_groups.append(
            HouseGroupSummary(
                house=num,
                house_keyword=hk,
                sign_on_cusp=sign_on,
                placements=placements,
            )
        )

    ctx = ChartContextSummary(
        shape=ChartShapeSummary(
            key=chart_shape_primary,
            interpretation=chart_shape_interpretation,
        ),
        concentration=dict(distribution),
        modality_element=dict(modality_element_distribution),
    )

    return InterpretationsSummary(
        house_groups=house_groups,
        chart_context=ctx,
        big_three=big_three_dict,
    )
