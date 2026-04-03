from typing import Any, Optional

from pydantic import BaseModel, Field


class MultilingualContent(BaseModel):
    en: str
    es: Optional[str] = None


class TarotCardLocalized(BaseModel):
    name_short: str
    name: str
    name_en: Optional[str] = Field(None, description="English display name from name.en")
    type: str
    value: str
    value_int: int
    meaning_up: str
    meaning_rev: str
    desc: str
    suit: Optional[str] = None
    image_path: Optional[str] = None


class DatabaseCard(BaseModel):
    name_short: str
    name: dict[str, Any]
    type: str
    value: dict[str, Any]
    value_int: int
    meaning_up: dict[str, Any]
    meaning_rev: dict[str, Any]
    description: dict[str, Any]
    suit: Optional[dict[str, Any]] = None
    image_path: Optional[str] = None


class PatchCardBody(BaseModel):
    name: Optional[dict[str, Any]] = None
    value: Optional[dict[str, Any]] = None
    meaning_up: Optional[dict[str, Any]] = None
    meaning_rev: Optional[dict[str, Any]] = None
    description: Optional[dict[str, Any]] = None
    suit: Optional[dict[str, Any]] = None


class TutorialSectionResponse(BaseModel):
    section_key: str
    title: str
    content: Any
