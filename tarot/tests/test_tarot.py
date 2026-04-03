import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from core.db.connection import AsyncSessionLocal, init_db
from main import app
from tarot.db.models import Card, Tutorial


def _sample_card_fool():
    return Card(
        name_short="ar00",
        name={"en": "The Fool", "es": "El Loco"},
        value={"en": "zero", "es": "cero"},
        meaning_up={"en": "up", "es": "arriba"},
        meaning_rev={"en": "rev", "es": "revés"},
        description={"en": "desc en", "es": "desc es"},
        suit=None,
        type_="major",
        value_int=0,
        image_path="/fool.jpg",
    )


def _sample_card_cups():
    return Card(
        name_short="cups02",
        name={"en": "Two of Cups", "es": "Dos de Copas"},
        value={"en": "two", "es": "dos"},
        meaning_up={"en": "bond", "es": "vínculo"},
        meaning_rev={"en": "split", "es": "ruptura"},
        description={"en": "pair", "es": "pareja"},
        suit={"en": "cups", "es": "cups"},
        type_="minor",
        value_int=42,
        image_path=None,
    )


async def _seed_tarot():
    await init_db()
    async with AsyncSessionLocal() as s:
        await s.execute(delete(Tutorial))
        await s.execute(delete(Card))
        s.add(_sample_card_fool())
        s.add(_sample_card_cups())
        s.add(
            Tutorial(
                section_key="intro",
                title={"en": "Intro", "es": "Intro ES"},
                content={"en": "Welcome", "es": "Bienvenido"},
                is_active=True,
                order_index=1,
            )
        )
        await s.commit()


@pytest.mark.asyncio
async def test_tarot_api_cards_and_tutorials():
    await _seed_tarot()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/cards", params={"lang": "en"})
        assert r.status_code == 200
        cards = r.json()
        assert len(cards) == 2
        assert cards[0]["name_short"] == "ar00"
        assert cards[0]["name"] == "The Fool"
        assert cards[0]["name_en"] == "The Fool"
        assert cards[0]["desc"] == "desc en"

        r_es = await ac.get("/api/cards", params={"lang": "es"})
        assert r_es.json()[0]["name"] == "El Loco"

        r2 = await ac.get("/api/cards/by-short/ar00")
        assert r2.status_code == 200
        assert r2.json()["type"] == "major"

        r404 = await ac.get("/api/cards/by-short/missing")
        assert r404.status_code == 404
        assert r404.json()["error"]

        rn = await ac.get("/api/cards/by-name", params={"name": "El Loco", "lang": "en"})
        assert rn.status_code == 200
        assert rn.json()["name_short"] == "ar00"

        rsearch = await ac.get("/api/cards/search", params={"q": "pair", "lang": "en"})
        assert len(rsearch.json()) == 1
        assert rsearch.json()[0]["name_short"] == "cups02"

        rempty = await ac.get("/api/cards/search", params={"q": "", "lang": "en"})
        assert rempty.json() == []

        rsuit = await ac.get("/api/cards/by-suit/cups")
        assert len(rsuit.json()) == 1

        rtype = await ac.get("/api/cards/by-type/minor")
        assert len(rtype.json()) == 1

        rt = await ac.get("/api/tutorials", params={"lang": "en"})
        assert len(rt.json()) == 1
        assert rt.json()[0]["section_key"] == "intro"

        rs = await ac.get("/api/tutorials/section/intro")
        assert rs.json()["title"] == "Intro"


@pytest.mark.asyncio
async def test_admin_cards_requires_auth():
    await _seed_tarot()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/admin/cards")
        assert r.status_code == 503

    import os

    os.environ["ADMIN_API_KEY"] = "secret"
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/api/admin/cards")
            assert r.status_code == 401
            r2 = await ac.get("/api/admin/cards", headers={"Authorization": "Bearer wrong"})
            assert r2.status_code == 401
            r3 = await ac.get("/api/admin/cards", headers={"Authorization": "Bearer secret"})
            assert r3.status_code == 200
            body = r3.json()
            assert len(body) == 2
            assert body[0]["name_short"] == "ar00"
            assert body[0]["name"]["en"] == "The Fool"
    finally:
        os.environ.pop("ADMIN_API_KEY", None)
