import pytest
from app.services.skip_action_services import skip_discard_and_draw
from app.core.database import database

@pytest.mark.asyncio
async def test_skip_discard_and_draw(monkeypatch):
    """
    Verifica que al no ejecutar acción:
      - Se descarte una carta aleatoria.
      - Se robe una nueva carta.
      - Devuelva la estructura esperada.
    """
    game_id = "game_1"
    player_id = "p1"

    # Datos falsos simulando estado de DB
    fake_hand = [
        {"id": 1, "game_id": game_id, "player_id": player_id, "type": "evidence", "name": "Gun"},
        {"id": 2, "game_id": game_id, "player_id": player_id, "type": "evidence", "name": "Knife"},
    ]
    fake_deck = [
        {"id": 100, "game_id": game_id, "type": "character", "name": "Poirot", "in_deck": True}
    ]

    # Mocks para reemplazar llamadas reales a DB
    async def fake_fetch_all(query):
        return fake_hand

    async def fake_fetch_one(query):
        return fake_deck[0]

    async def fake_execute(query):
        return None

    async def fake_fetch_val(query):
        return 6  # total final de cartas (no importa el número exacto)

    # Aplicar mocks
    monkeypatch.setattr(database, "fetch_all", fake_fetch_all)
    monkeypatch.setattr(database, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(database, "execute", fake_execute)
    monkeypatch.setattr(database, "fetch_val", fake_fetch_val)

    # Ejecutar la lógica de descarte
    result = await skip_discard_and_draw(game_id, player_id)

    # Verificaciones
    assert result["discarded"] is not None
    assert result["drawn"] is not None
    assert result["final_hand_count"] == 6
    assert "type" in result["discarded"]
    assert "name" in result["drawn"]