from typing import Literal, Optional

from pydantic import BaseModel, Field


class TarotCard(BaseModel):
    """Minimal tarot card model for API responses."""

    id: int = Field(..., description="Stable index in deck order (1–78)")
    name: str
    arcana: Literal["major", "minor"]
    suit: Optional[str] = Field(None, description="wands, cups, swords, pentacles for minor arcana")
