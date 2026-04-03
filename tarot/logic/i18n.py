from typing import Any, Optional


def pick_lang(content: Optional[Any], lang: str) -> str:
    """
    Resolve multilingual JSONB-style dict: content[lang] ?? content['en'] ?? ''.
    If content is not a dict, returns str(content) or empty.
    """
    if content is None:
        return ""
    if not isinstance(content, dict):
        return str(content) if content is not None else ""
    v = content.get(lang)
    if v is not None and isinstance(v, str):
        return v
    v = content.get("en")
    if v is not None and isinstance(v, str):
        return v
    return ""
