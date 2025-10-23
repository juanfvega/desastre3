import pytest
import asyncio

from sqlalchemy import insert
from app.services import cards_effects_services as card_services
from app.core.database import database
from app.models.hand import player_hands
from app.models.detective_sets import detective_sets

@pytest.mark.asyncio
async def test_can_play_detective_card():
    game_id = "dummy_game"
    player_id = "dummyP1"
    card_name = "detective_brent"

    # Limpiar tablas
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})

    # Mano del jugador
    dummy_hand = [
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_brent"},
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_quin"},
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "detective_pyne"},
    ]
    await database.execute_many(player_hands.insert(), dummy_hand)

    # No hay sets en mesa aún
    result = await card_services.can_play_card(game_id, player_id, card_name)
    assert result["can_play"] is True
    assert result["by_hand"] is True
    assert result["by_table"] is False

    # Crear un set de detectives en mesa
    await database.execute(insert(detective_sets).values(
        game_id=game_id, player_id=player_id, detective_name="detective_brent", set_size=2
    ))

    result2 = await card_services.can_play_card(game_id, player_id, card_name)
    assert result2["can_play"] is True
    assert result2["by_table"] is True

    # Limpiar datos
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM detective_sets WHERE game_id = :gid", {"gid": game_id})
