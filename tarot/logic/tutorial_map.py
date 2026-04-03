from __future__ import annotations

from typing import Any

from tarot.db.models import Tutorial
from tarot.logic.i18n import pick_lang
from tarot.schema.api_types import TutorialSectionResponse


def pick_lang_content(content: Any, lang: str) -> Any:
    """Tutorial content may be a string per locale or arbitrary JSON per locale."""
    if content is None:
        return None
    if not isinstance(content, dict):
        return content
    if lang in content:
        return content[lang]
    if "en" in content:
        return content["en"]
    return content


def row_to_tutorial(row: Tutorial, lang: str) -> TutorialSectionResponse:
    return TutorialSectionResponse(
        section_key=row.section_key,
        title=pick_lang(row.title, lang),
        content=pick_lang_content(row.content, lang),
    )
