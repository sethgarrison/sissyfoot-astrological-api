"""Pydantic schemas for data table updates. All fields optional for PATCH."""
from typing import Optional

from pydantic import BaseModel, Field


# --- Reference tables ---

class PlanetUpdate(BaseModel):
    symbol: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None


class SignUpdate(BaseModel):
    element: Optional[str] = None
    modality: Optional[str] = None
    archetypes_balanced: Optional[str] = None
    archetypes_unbalanced: Optional[str] = None
    journey: Optional[str] = None
    gifts: Optional[str] = None
    challenges: Optional[str] = None
    interpretation: Optional[str] = None


class HouseUpdate(BaseModel):
    type_: Optional[str] = Field(None, alias="type")
    description: Optional[str] = None
    subtitle: Optional[str] = None
    keywords: Optional[str] = None

    model_config = {"populate_by_name": True}


class AspectUpdate(BaseModel):
    angle_degrees: Optional[int] = None
    symbol: Optional[str] = None
    type_: Optional[str] = Field(None, alias="type")

    model_config = {"populate_by_name": True}


# --- Big Three ---

class SunSignInterpretationUpdate(BaseModel):
    archetypes_balanced: Optional[str] = None
    archetypes_unbalanced: Optional[str] = None
    journey: Optional[str] = None
    gifts: Optional[str] = None
    challenges: Optional[str] = None
    interpretation: Optional[str] = None


class MoonSignInterpretationUpdate(BaseModel):
    nature: Optional[str] = None
    sources_of_contentment: Optional[str] = None
    keywords: Optional[str] = None
    interpretation: Optional[str] = None


class AscendantSignInterpretationUpdate(BaseModel):
    impression: Optional[str] = None
    appearance: Optional[str] = None
    childhood: Optional[str] = None
    balance: Optional[str] = None
    interpretation: Optional[str] = None


# --- Interpretation tables ---

class PlanetSignInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None
    interpretation_long: Optional[str] = None
    interpretation_short: Optional[str] = None
    keywords: Optional[str] = None
    retrograde_interpretation: Optional[str] = None


class PlanetHouseInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None
    short_interpretation: Optional[str] = None
    retrograde_interpretation: Optional[str] = None


class AspectTypeInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None


class AspectInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None


class PlanetAspectInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None


class SignHouseInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None


class ChartShapeInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None


class ChartDistributionInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None


class ModalityElementDistributionInterpretationUpdate(BaseModel):
    interpretation_text: Optional[str] = None
