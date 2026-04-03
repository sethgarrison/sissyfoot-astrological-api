from __future__ import annotations

import os
from typing import Optional
import random
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from tarot.db.models import Card, Tutorial
from tarot.logic.card_map import merge_json_field, row_to_database_card, row_to_localized
from tarot.logic.i18n import pick_lang
from tarot.logic.tutorial_map import row_to_tutorial
from tarot.schema.api_types import DatabaseCard, PatchCardBody, TarotCardLocalized, TutorialSectionResponse

router = APIRouter(prefix="/api", tags=["tarot-api"])


def _admin_guard(request: Request) -> Optional[JSONResponse]:
    key = os.environ.get("ADMIN_API_KEY")
    if not key:
        return JSONResponse(status_code=503, content={"error": "Admin API not configured"})
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer ") or auth[7:] != key:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return None


def _name_dict(card: Card) -> dict:
    n = card.name
    return n if isinstance(n, dict) else {}


def _suit_dict(card: Card) -> dict:
    s = card.suit
    return s if isinstance(s, dict) else {}


# --- Public cards ---


@router.get("/cards", response_model=list[TarotCardLocalized])
async def list_cards(
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Card).order_by(Card.name_short.asc())
    rows = (await session.scalars(stmt)).all()
    return [row_to_localized(r, lang) for r in rows]


@router.get("/cards/by-name", response_model=TarotCardLocalized)
async def card_by_name(
    name: str = Query(..., description="Match name.en or name.es exactly"),
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Card)
    rows = (await session.scalars(stmt)).all()
    for row in rows:
        d = _name_dict(row)
        if d.get("en") == name or d.get("es") == name:
            return row_to_localized(row, lang)
    return JSONResponse(status_code=404, content={"error": "Card not found"})


@router.get("/cards/by-name-lang", response_model=TarotCardLocalized)
async def card_by_name_lang(
    name: str = Query(..., description="Match name.en only"),
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Card)
    rows = (await session.scalars(stmt)).all()
    for row in rows:
        if _name_dict(row).get("en") == name:
            return row_to_localized(row, lang)
    return JSONResponse(status_code=404, content={"error": "Card not found"})


@router.get("/cards/by-short/{name_short}", response_model=TarotCardLocalized)
async def card_by_short(
    name_short: str,
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    row = await session.get(Card, name_short)
    if not row:
        return JSONResponse(status_code=404, content={"error": "Card not found"})
    return row_to_localized(row, lang)


@router.get("/cards/random", response_model=TarotCardLocalized)
async def card_random(
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Card).order_by(func.random()).limit(1)
    row = (await session.scalars(stmt)).first()
    if not row:
        return JSONResponse(status_code=404, content={"error": "No cards in database"})
    return row_to_localized(row, lang)


@router.get("/cards/random-many", response_model=list[TarotCardLocalized])
async def card_random_many(
    count: int = Query(1, ge=1, le=200),
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Card)
    rows = list((await session.scalars(stmt)).all())
    if not rows:
        return []
    random.shuffle(rows)
    n = min(count, len(rows))
    return [row_to_localized(r, lang) for r in rows[:n]]


@router.get("/cards/by-suit/{suit}", response_model=list[TarotCardLocalized])
async def cards_by_suit(
    suit: str,
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Card).order_by(Card.value_int.asc())
    rows = (await session.scalars(stmt)).all()
    return [
        row_to_localized(r, lang)
        for r in rows
        if _suit_dict(r).get("en") == suit
    ]


@router.get("/cards/by-type/{card_type}", response_model=list[TarotCardLocalized])
async def cards_by_type(
    card_type: str,
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    ct = card_type.lower()
    if ct not in ("major", "minor"):
        return JSONResponse(
            status_code=400,
            content={"error": "type must be major or minor"},
        )
    stmt = select(Card).where(Card.type_ == ct).order_by(Card.value_int.asc())
    rows = (await session.scalars(stmt)).all()
    return [row_to_localized(r, lang) for r in rows]


@router.get("/cards/search", response_model=list[TarotCardLocalized])
async def cards_search(
    q: str = Query(""),
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    if not q or not q.strip():
        return []
    needle = q.strip().lower()
    stmt = select(Card).order_by(Card.name_short.asc())
    rows = (await session.scalars(stmt)).all()
    out: list[TarotCardLocalized] = []
    for row in rows:
        hay = [
            pick_lang(row.name, "en"),
            pick_lang(row.name, "es"),
            pick_lang(row.description, "en"),
            pick_lang(row.description, "es"),
        ]
        if any(needle in (h or "").lower() for h in hay):
            out.append(row_to_localized(row, lang))
    return out


# --- Tutorials ---


@router.get("/tutorials", response_model=list[TutorialSectionResponse])
async def list_tutorials(
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Tutorial)
        .where(Tutorial.is_active.is_(True))
        .order_by(Tutorial.order_index.asc())
    )
    rows = (await session.scalars(stmt)).all()
    return [row_to_tutorial(r, lang) for r in rows]


@router.get("/tutorials/section/{section_key}", response_model=TutorialSectionResponse)
async def tutorial_section(
    section_key: str,
    lang: str = Query("en"),
    session: AsyncSession = Depends(get_db),
):
    row = await session.get(Tutorial, section_key)
    if not row or not row.is_active:
        return JSONResponse(status_code=404, content={"error": "Tutorial not found"})
    return row_to_tutorial(row, lang)


# --- Admin ---


@router.get("/admin/cards", response_model=list[DatabaseCard])
async def admin_list_cards(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    if bad := _admin_guard(request):
        return bad
    stmt = select(Card).order_by(Card.value_int.asc())
    rows = (await session.scalars(stmt)).all()
    return [row_to_database_card(r) for r in rows]


@router.patch("/admin/cards/{name_short}")
async def admin_patch_card(
    name_short: str,
    request: Request,
    body: PatchCardBody,
    session: AsyncSession = Depends(get_db),
):
    if bad := _admin_guard(request):
        return bad
    row = await session.get(Card, name_short)
    if not row:
        return JSONResponse(status_code=404, content={"error": "Card not found"})
    data = body.model_dump(exclude_unset=True)
    for field in (
        "name",
        "value",
        "meaning_up",
        "meaning_rev",
        "description",
        "suit",
    ):
        if field in data and data[field] is not None:
            merged = merge_json_field(getattr(row, field), data[field])
            setattr(row, field, merged)
    await session.flush()
    return {"ok": True}


# --- Optional health ---


@router.get("/health")
async def api_health(session: AsyncSession = Depends(get_db)):
    try:
        await session.scalar(select(func.count()).select_from(Card))
        db_ok = True
    except Exception:
        db_ok = False
    return {"ok": True, "db": db_ok}
