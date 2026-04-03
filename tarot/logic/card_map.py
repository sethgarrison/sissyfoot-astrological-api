from __future__ import annotations

from typing import Any, Optional

from tarot.db.models import Card
from tarot.logic.i18n import pick_lang
from tarot.schema.api_types import DatabaseCard, TarotCardLocalized


def row_to_localized(row: Card, lang: str) -> TarotCardLocalized:
    name_en = pick_lang(row.name, "en")
    return TarotCardLocalized(
        name_short=row.name_short,
        name=pick_lang(row.name, lang),
        name_en=name_en or None,
        type=row.type_,
        value=pick_lang(row.value, lang),
        value_int=row.value_int,
        meaning_up=pick_lang(row.meaning_up, lang),
        meaning_rev=pick_lang(row.meaning_rev, lang),
        desc=pick_lang(row.description, lang),
        suit=pick_lang(row.suit, lang) if row.suit else None,
        image_path=row.image_path,
    )


def row_to_database_card(row: Card) -> DatabaseCard:
    return DatabaseCard(
        name_short=row.name_short,
        name=dict(row.name) if isinstance(row.name, dict) else {},
        type=row.type_,
        value=dict(row.value) if isinstance(row.value, dict) else {},
        value_int=row.value_int,
        meaning_up=dict(row.meaning_up) if isinstance(row.meaning_up, dict) else {},
        meaning_rev=dict(row.meaning_rev) if isinstance(row.meaning_rev, dict) else {},
        description=dict(row.description) if isinstance(row.description, dict) else {},
        suit=dict(row.suit) if isinstance(row.suit, dict) else None,
        image_path=row.image_path,
    )


def merge_json_field(existing: Optional[Any], patch: Optional[dict]) -> dict:
    """Shallow-merge patch into existing dict for i18n fields."""
    if patch is None:
        return dict(existing) if isinstance(existing, dict) else {}
    base = dict(existing) if isinstance(existing, dict) else {}
    for k, v in patch.items():
        if v is not None:
            base[k] = v
    return base
