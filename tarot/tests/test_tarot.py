from fastapi.testclient import TestClient

from main import app


def test_tarot_cards_returns_full_deck():
    client = TestClient(app)
    r = client.get("/tarot/cards")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 78
    assert data[0]["name"] == "The Fool"
    assert data[0]["arcana"] == "major"
    assert data[21]["name"] == "The World"
    assert data[22]["arcana"] == "minor"
    assert data[22]["suit"] is not None
