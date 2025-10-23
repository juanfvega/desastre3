import pytest
import asyncio
from sqlalchemy import insert
from app.services import cards_effects_services as card_services
from app.core.database import database
from app.models.hand import player_hands
from app.models.detective_sets import detective_sets
from app.models.card import PlayCardRequest

@pytest.mark.asyncio
async def test_play_detective_set():
    game_id = "dummy_game"
    player_id = "dummyP1"
    card_name = "detective_brent"

    # Limpiar tablas
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})

    # Mano del jugador con suficientes cartas y un comodín
    dummy_hand = [
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_brent"},
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_quin"},
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_pyne"},
    ]
    await database.execute_many(player_hands.insert(), dummy_hand)

    # Jugar carta
    extra_data = PlayCardRequest(player_hand=True)
    result = await card_services.play_card(game_id, player_id, card_name, extra_data=extra_data)
    assert result is not None

    # Verificar que el set se creó
    sets = await database.fetch_all(
        detective_sets.select().where(
            (detective_sets.c.game_id == game_id)
            & (detective_sets.c.player_id == player_id)
            & (detective_sets.c.detective_name == card_name)
        )
    )
    assert len(sets) == 1
    assert sets[0]["set_size"] == 2

    # Verificar que las cartas usadas se eliminaron de la mano
    remaining_hand = await database.fetch_all(
        player_hands.select().where(
            (player_hands.c.game_id == game_id)
            & (player_hands.c.player_id == player_id)
        )
    )
    remaining_names = [c["name"] for c in remaining_hand]
    assert "detective_brent" not in remaining_names
    # Comodín Quin usado para completar set, por lo que también se eliminó
    assert "detective_quin" not in remaining_names
    # La carta que no se usó permanece
    assert "detective_pyne" in remaining_names

    # Limpiar datos
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})

@pytest.mark.asyncio
async def test_play_detective_set_no_joker_needed():
    game_id = "dummy_game2"
    player_id = "dummyP2"
    card_name = "detective_brent"

    # Limpiar tablas
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})

    # Mano del jugador con suficientes cartas del mismo tipo + 1 comodín
    dummy_hand = [
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_brent"},
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_brent"},  # segunda carta
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_quin"},   # comodín, no debería usarse
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_pyne"},
    ]
    await database.execute_many(player_hands.insert(), dummy_hand)

    # Jugar carta
    extra_data = PlayCardRequest(player_hand=True)
    result = await card_services.play_card(game_id, player_id, card_name, extra_data=extra_data)
    assert result is not None

    # Verificar que el set se creó
    sets = await database.fetch_all(
        detective_sets.select().where(
            (detective_sets.c.game_id == game_id)
            & (detective_sets.c.player_id == player_id)
            & (detective_sets.c.detective_name == card_name)
        )
    )
    assert len(sets) == 1
    # El tamaño del set sigue siendo 2 (las cartas “reales” cubren el requisito)
    assert sets[0]["set_size"] == 2

    # Verificar que las cartas usadas se eliminaron de la mano
    remaining_hand = await database.fetch_all(
        player_hands.select().where(
            (player_hands.c.game_id == game_id)
            & (player_hands.c.player_id == player_id)
        )
    )
    remaining_names = [c["name"] for c in remaining_hand]
    # Cartas “reales” usadas
    assert remaining_names.count("detective_brent") == 0
    # Comodín no se usó
    assert "detective_quin" in remaining_names
    # Carta que no se usó
    assert "detective_pyne" in remaining_names

    # Limpiar datos
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})
