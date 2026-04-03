from tarot.schema.card import TarotCard

_MAJOR_ARCANA: list[str] = [
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
]

_RANKS: list[str] = [
    "Ace",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Page",
    "Knight",
    "Queen",
    "King",
]

_SUITS: list[tuple[str, str]] = [
    ("wands", "Wands"),
    ("cups", "Cups"),
    ("swords", "Swords"),
    ("pentacles", "Pentacles"),
]


def static_rider_waite_smith_deck() -> list[TarotCard]:
    """Full 78-card deck metadata (static reference data)."""
    cards: list[TarotCard] = []
    n = 1
    for name in _MAJOR_ARCANA:
        cards.append(TarotCard(id=n, name=name, arcana="major", suit=None))
        n += 1
    for suit_key, suit_label in _SUITS:
        for rank in _RANKS:
            cards.append(
                TarotCard(
                    id=n,
                    name=f"{rank} of {suit_label}",
                    arcana="minor",
                    suit=suit_key,
                )
            )
            n += 1
    return cards


STATIC_FULL_DECK: list[TarotCard] = static_rider_waite_smith_deck()
