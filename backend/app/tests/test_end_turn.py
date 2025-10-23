import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.main import app
from app.core.database import database
from app.services import game_service
from app.models.game import GameStatus
from app.models.hand import player_hands
import uuid


# --- FIX: aseguramos compatibilidad con columnas nuevas sin tocar backend ---
@pytest_asyncio.fixture(autouse=True)
async def ensure_columns_exist():
    """
    Si otras épicas agregaron columnas nuevas (turn_phase, last_action, etc.),
    las creamos silenciosamente solo en la DB de tests.
    """
    columns = [
        "turn_phase TEXT DEFAULT 'ACTION'",
        "last_action TEXT DEFAULT 'NONE'",
        "deck_initialized BOOLEAN DEFAULT 0"
    ]
    for c in columns:
        try:
            await database.execute(text(f"ALTER TABLE games ADD COLUMN {c}"))
        except Exception:
            pass
    yield


# --- Cliente HTTP para pytest ---
@pytest_asyncio.fixture
async def async_client():
    """Cliente HTTP asíncrono compatible con httpx >= 0.28"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Monkeypatch temporal: versión simple de create_game ---
async def _legacy_create_game(nameGame, num_players, host):
    """
    Implementación mínima de create_game (sin campos nuevos)
    usada solo para estos tests de Story 16.
    No toca el código real de game_service.
    """
    game_id = str(uuid.uuid4())
    query = """
        INSERT INTO games (id, nameGame, num_players, host, status, current_turn_player, players)
        VALUES (:id, :name, :nplayers, :host, :status, :turn, :players)
    """
    await database.execute(query, {
        "id": game_id,
        "name": nameGame,
        "nplayers": num_players,
        "host": host,
        "status": "PLAYING",
        "turn": host,
        "players": '["player1","player2","player3"]'
    })
    return {
        "id": game_id,
        "nameGame": nameGame,
        "num_players": num_players,
        "host": host
    }


@pytest_asyncio.fixture(autouse=True)
def patch_create_game(monkeypatch):
    """Reemplaza temporalmente create_game por la versión simplificada."""
    monkeypatch.setattr(game_service, "create_game", _legacy_create_game)
    yield


# --- TESTS Story 16: Terminar turno ---

@pytest.mark.asyncio
async def test_end_turn_success(async_client):
    """
    Caso correcto: jugador activo termina turno correctamente.
    """
    game = await game_service.create_game("TestTurno", 3, "player1")
    game_id = game["id"]

    # Insertar 6 cartas simuladas en la mano del jugador activo
    for i in range(6):
        await database.execute(
            player_hands.insert().values(
                game_id=game_id,
                player_id="player1",
                type="Detective",
                name=f"card_{i}",
            )
        )

    response = await async_client.post(
        f"/api/games/{game_id}/turns/end",
        json={"player_id": "player1"}
    )

    data = response.json()
    assert response.status_code == 200
    assert data["success"] is True
    assert data["previous_player"] == "player1"
    assert data["next_player"] == "player2"


@pytest.mark.asyncio
async def test_end_turn_not_active_player(async_client):
    """
    Caso incorrecto: jugador que no es el activo intenta terminar turno.
    """
    game = await game_service.create_game("TurnFail", 2, "playerA")
    game_id = game["id"]

    # Insertar cartas válidas en jugador activo
    for i in range(6):
        await database.execute(
            player_hands.insert().values(
                game_id=game_id,
                player_id="playerA",
                type="Detective",
                name=f"card_{i}",
            )
        )

    response = await async_client.post(
        f"/api/games/{game_id}/turns/end",
        json={"player_id": "playerB"}
    )

    assert response.status_code == 403
    assert "Not your turn" in response.text


@pytest.mark.asyncio
async def test_end_turn_wrong_card_count(async_client):
    """
    Caso incorrecto: jugador activo no tiene 6 cartas al terminar turno.
    """
    game = await game_service.create_game("TurnWrongCards", 2, "p1")
    game_id = game["id"]

    # Solo 5 cartas
    for i in range(5):
        await database.execute(
            player_hands.insert().values(
                game_id=game_id,
                player_id="p1",
                type="Detective",
                name=f"card_{i}",
            )
        )

    response = await async_client.post(
        f"/api/games/{game_id}/turns/end",
        json={"player_id": "p1"}
    )

    assert response.status_code == 400
    assert "6 cards" in response.text
