"""
Placeholder detection and interpretation source metadata.
Used to identify whether interpretation data came from DB vs defaults,
and whether content is a "fill-in" placeholder vs real content.
"""
import re

# Substrings that indicate placeholder / "add your content" text
PLACEHOLDER_PATTERNS = [
    "[Add interpretation",
    "[Add your interpretation",
    "[Add interpretation for",
]


def is_placeholder_text(text: str | None) -> bool:
    """True if text matches known placeholder patterns (e.g. '[Add interpretation...]')."""
    if not text or not isinstance(text, str):
        return False
    t = text.strip()
    return any(p in t for p in PLACEHOLDER_PATTERNS)
