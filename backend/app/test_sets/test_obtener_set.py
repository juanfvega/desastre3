import pytest
from app.main import app  # tu FastAPI instance
from app.core.database import database
from app.models.detective_sets import detective_sets
from app.models.player import players_table
from app.services import card_services

@pytest.mark.asyncio
async def test_get_sets_endpoint():
    game_id = "test_game"
    player1_id = "player1"
    player2_id = "player2"

    # Limpiar tablas
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM players WHERE id IN (:p1,:p2)", {"p1": player1_id, "p2": player2_id})

    # Insertar jugadores
    await database.execute_many(players_table.insert(), [
        {"id": player1_id, "username": "Jugador1"},
        {"id": player2_id, "username": "Jugador2"}
    ])

    # Insertar sets
    await database.execute_many(detective_sets.insert(), [
        {
            "game_id": game_id,
            "player_id": player1_id,
            "detective_name": "detective_poirot",
            "set_size": 2,
            "cards_used": ["detective_quin", "detective_poirot"]
        },
        {
            "game_id": game_id,
            "player_id": player2_id,
            "detective_name": "detective_marple",
            "set_size": 3,
            "cards_used": ["detective_marple", "detective_marple", "detective_marple"]
        }
    ])

    result = await card_services.get_detective_sets_by_game(game_id)

    # Verificar estructura
    assert "Jugador1" in result
    assert "Jugador2" in result
    assert len(result["Jugador1"]) == 1
    assert len(result["Jugador2"]) == 1

    # Verificar reordenamiento de comodín
    player1_cards = result["Jugador1"][0]["cards"]
    assert player1_cards[-1]["name"] == "detective_quin"
    assert player1_cards[0]["name"] == "detective_poirot"

    # Verificar contenido del set de Jugador2
    player2_cards = result["Jugador2"][0]["cards"]
    assert [c["name"] for c in player2_cards] == ["detective_marple", "detective_marple", "detective_marple"]

    # Limpiar tablas
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM players WHERE id IN (:p1,:p2)", {"p1": player1_id, "p2": player2_id})
