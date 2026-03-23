"""Pydantic models for interpretations_summary on NatalChart."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PlacementLongTexts(BaseModel):
    in_sign: Optional[str] = None
    in_house: Optional[str] = None


class SummaryAspectItem(BaseModel):
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


class SummaryPlacement(BaseModel):
    body: str
    sign: str
    sign_adverb: str
    planet_keyword: Optional[str] = None
    synthesis: str
    retrograde: bool = False
    aspects: list[SummaryAspectItem] = Field(default_factory=list)
    long: Optional[PlacementLongTexts] = None


class HouseGroupSummary(BaseModel):
    house: int
    house_keyword: Optional[str] = None
    sign_on_cusp: str = ""
    placements: list[SummaryPlacement] = Field(default_factory=list)


class ChartShapeSummary(BaseModel):
    key: Optional[str] = None
    interpretation: Optional[str] = None


class ChartContextSummary(BaseModel):
    shape: ChartShapeSummary = Field(default_factory=ChartShapeSummary)
    concentration: dict[str, str] = Field(default_factory=dict)
    modality_element: dict[str, str] = Field(default_factory=dict)


class InterpretationsSummary(BaseModel):
    house_groups: list[HouseGroupSummary] = Field(default_factory=list)
    chart_context: ChartContextSummary = Field(default_factory=ChartContextSummary)
    big_three: dict = Field(default_factory=dict)  # sun/moon/ascendant blobs; filled from BigThree.model_dump()
