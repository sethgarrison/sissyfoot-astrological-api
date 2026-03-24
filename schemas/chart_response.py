"""
Public chart API response: chart_data (raw, for drawing) + interpretation (readings only).
Matches the client contract; fields may grow over time.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Chart core (computation pipeline; not the wire format) ---


class PlanetPosition(BaseModel):
    name: str
    sign: str
    sign_num: int
    degree: float
    abs_degree: float
    house: int
    retrograde: bool
    speed: Optional[float] = None


class HouseCusp(BaseModel):
    number: int
    sign: str
    degree: float
    abs_degree: float


class LunarNodePosition(BaseModel):
    node: str
    sign: str
    sign_num: int
    degree: float
    abs_degree: float
    house: int


class AspectData(BaseModel):
    planet1: str
    planet2: str
    aspect: str
    aspect_degrees: int
    orbit: float
    movement: str = ""
    type: Optional[str] = None
    interpretation: Optional[str] = None
    source: Optional[str] = None
    is_placeholder: bool = False


class LunarPhaseData(BaseModel):
    degrees_between: float
    phase_name: str
    emoji: str


class ChartDataDistributionBucket(BaseModel):
    count: int
    signs: list[str] = Field(default_factory=list)
    planets: list[str] = Field(default_factory=list)
    interpretation: Optional[str] = None


class QualityDistributionData(BaseModel):
    cardinal: ChartDataDistributionBucket
    fixed: ChartDataDistributionBucket
    mutable: ChartDataDistributionBucket


class ElementDistributionData(BaseModel):
    fire: ChartDataDistributionBucket
    earth: ChartDataDistributionBucket
    air: ChartDataDistributionBucket
    water: ChartDataDistributionBucket


class ChartData(BaseModel):
    """Raw chart facts + distribution counts for drawing only — not for interpretive copy."""

    aspects: list[AspectData]
    planets: list[PlanetPosition]
    lunar_nodes: list[LunarNodePosition]
    houses: list[HouseCusp]
    by_quality: QualityDistributionData
    by_element: ElementDistributionData
    lunar_phase: LunarPhaseData


# --- Interpretation (readings UI) ---


class SunInterpretation(BaseModel):
    sign: str
    archetypes_balanced: str = ""
    archetypes_unbalanced: str = ""
    journey: str = ""
    gifts: str = ""
    challenges: str = ""
    interpretation: str = ""


class MoonInterpretation(BaseModel):
    sign: str
    nature: str = ""
    sources_of_contentment: str = ""
    keywords: Optional[str] = None
    interpretation: str = ""


class RisingInterpretation(BaseModel):
    sign: str
    impression: str = ""
    appearance: str = ""
    childhood: str = ""
    balance: str = ""
    interpretation: str = ""


class ChartInterpretationsBigThree(BaseModel):
    sun: SunInterpretation
    moon: MoonInterpretation
    ascendant: RisingInterpretation


class ChartInterpretationsShape(BaseModel):
    key: str = ""
    interpretation: str = ""


class KeyedInterpretation(BaseModel):
    key: str = ""
    interpretation: str = ""


class ContextInterpretation(BaseModel):
    shape: ChartInterpretationsShape
    spatial_distribution: KeyedInterpretation
    quality_distribution: KeyedInterpretation
    modality_distribution: KeyedInterpretation


class HouseGroupInterpretationText(BaseModel):
    house_in_sign: str = ""


class AspectInterpretation(BaseModel):
    aspect: str
    aspect_type: Optional[str] = None
    aspect_keyphrase: Optional[str] = None
    other_body: str
    other_sign: str
    other_planet_keyword: Optional[str] = None
    other_sign_adverb: Optional[str] = None
    synthesis: str
    interpretation: Optional[str] = None
    is_placeholder: bool = False


class PlanetInterpretationText(BaseModel):
    planet_in_sign: str = ""
    planet_in_house: str = ""


class PlanetInterpretation(BaseModel):
    body: str
    sign: str
    sign_adverb: str = ""
    planet_keyword: str = ""
    synthesis: str
    retrograde: bool = False
    aspects: list[AspectInterpretation] = Field(default_factory=list)
    interpretation: PlanetInterpretationText


class HouseInterpretation(BaseModel):
    house: int
    house_keyword: str = ""
    sign_on_cusp: str = ""
    interpretation: HouseGroupInterpretationText
    planets: list[PlanetInterpretation] = Field(default_factory=list)


class ChartInterpretation(BaseModel):
    big_three: ChartInterpretationsBigThree
    context: ContextInterpretation
    house_groups: list[HouseInterpretation] = Field(default_factory=list)
    retrograde_planets: list[str] = Field(default_factory=list)
    retrograde_interpretations: Any = Field(default_factory=dict)


class ChartAPIResponse(BaseModel):
    name: str = ""
    birth_datetime: str
    latitude: float
    longitude: float
    house_system: str = "whole_sign"
    sun_sign: str
    moon_sign: str
    rising_sign: str
    chart_data: ChartData
    interpretation: ChartInterpretation
    reading_id: Optional[str] = None


class QualityDistribution(BaseModel):
    count: int
    signs: list[str] = Field(default_factory=list)
    planets: list[str] = Field(default_factory=list)


class ElementDistribution(BaseModel):
    count: int
    signs: list[str] = Field(default_factory=list)
    planets: list[str] = Field(default_factory=list)


class SignPlacementOverview(BaseModel):
    signs_with_planets: dict[str, list[str]] = Field(default_factory=dict)
    by_quality: dict[str, QualityDistribution] = Field(default_factory=dict)
    by_element: dict[str, ElementDistribution] = Field(default_factory=dict)


class ChartCore(BaseModel):
    """Ephemeris + overview; used only server-side before building ChartAPIResponse."""

    name: Optional[str] = None
    birth_datetime: str
    latitude: float
    longitude: float
    house_system: str = "whole_sign"
    sun_sign: str
    moon_sign: str
    rising_sign: str
    lunar_phase: LunarPhaseData
    planets: list[PlanetPosition]
    lunar_nodes: list[LunarNodePosition] = Field(default_factory=list)
    houses: list[HouseCusp]
    houses_overview: SignPlacementOverview
    aspects: list[AspectData]
