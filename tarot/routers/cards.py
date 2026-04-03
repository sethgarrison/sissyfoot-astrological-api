from fastapi import APIRouter

from tarot.logic.deck import STATIC_FULL_DECK
from tarot.schema.card import TarotCard

router = APIRouter(prefix="/tarot", tags=["tarot"])


@router.get("/cards", response_model=list[TarotCard])
def list_cards() -> list[TarotCard]:
    """Return the full 78-card deck metadata (static; proof-of-concept)."""
    return STATIC_FULL_DECK
