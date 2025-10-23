import pytest
from app.core.database import database
from app.services.auto_discard_service import auto_discard_if_needed
from app.models.hand import player_hands
from app.models.deck import deck_cards


@pytest.mark.asyncio
async def test_auto_discard_more_than_6():
    """Jugador con más de 6 cartas → descarta hasta 6"""
    game_id = "g1"
    player_id = "p1"

    await database.execute("DELETE FROM player_hands")
    await database.execute("DELETE FROM deck_cards")

    # Crear mano de 8 cartas (sin tocar el ID)
    for i in range(8):
        await database.execute(
            player_hands.insert().values(
                game_id=game_id,
                player_id=player_id,
                type="event",
                name=f"Card{i}",
            )
        )

    result = await auto_discard_if_needed(game_id, player_id)
    assert result["final_hand_count"] == 6
    assert len(result["discarded"]) == 2
    assert len(result["drawn"]) == 0


@pytest.mark.asyncio
async def test_auto_discard_equal_6():
    """Jugador con 6 cartas → descarta 1 y roba 1"""
    game_id = "g2"
    player_id = "p2"

    await database.execute("DELETE FROM player_hands")
    await database.execute("DELETE FROM deck_cards")

    # Crear mano de 6 cartas (sin ID manual)
    for i in range(6):
        await database.execute(
            player_hands.insert().values(
                game_id=game_id,
                player_id=player_id,
                type="event",
                name=f"Card{i}",
            )
        )

    # Crear mazo con 10 cartas (sin ID manual)
    for j in range(10):
        await database.execute(
            deck_cards.insert().values(
                game_id=game_id,
                type="event",
                name=f"Deck{j}",
                in_deck=True,
            )
        )

    result = await auto_discard_if_needed(game_id, player_id)
    assert result["final_hand_count"] == 6
    assert len(result["discarded"]) == 1
    assert len(result["drawn"]) == 1


@pytest.mark.asyncio
async def test_auto_discard_less_than_6():
    """Jugador con menos de 6 cartas → roba hasta 6"""
    game_id = "g3"
    player_id = "p3"

    await database.execute("DELETE FROM player_hands")
    await database.execute("DELETE FROM deck_cards")

    # Crear mano de 4 cartas
    for i in range(4):
        await database.execute(
            player_hands.insert().values(
                game_id=game_id,
                player_id=player_id,
                type="event",
                name=f"Card{i}",
            )
        )

    # Crear mazo con 5 cartas
    for j in range(5):
        await database.execute(
            deck_cards.insert().values(
                game_id=game_id,
                type="event",
                name=f"Deck{j}",
                in_deck=True,
            )
        )

    result = await auto_discard_if_needed(game_id, player_id)
    assert result["final_hand_count"] == 6
    assert len(result["drawn"]) == 2
    assert len(result["discarded"]) == 0
