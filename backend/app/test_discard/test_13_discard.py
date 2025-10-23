import pytest
import asyncio
from app.services import card_services
from app.core.database import database
from app.models.deck import deck_cards
from app.models.hand import player_hands

@pytest.mark.asyncio
async def test_discard():
    game_id = "dummy_deck"
    player1_id = "dummyP1"
    player2_id = "dummyP2"
    card_name = "detective_brent"

    # 0. Limpiar cualquier rastro previo
    await database.execute("DELETE FROM deck_cards WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})

    # 1. Crear mazo dummy
    dummy_cards = [
        {"game_id": game_id, "type": "detective", "name": "detective_brent", "in_deck": None, "in_card_draft": 1},  # draft, no descartable
        {"game_id": game_id, "type": "detective", "name": "detective_brent", "in_deck": None, "in_card_draft": 0},  # descartable
        {"game_id": game_id, "type": "detective", "name": "detective_brent", "in_deck": None, "in_card_draft": 0},  # otra que puede descartarse
        {"game_id": game_id, "type": "detective", "name": "detective_brent", "in_deck": True, "in_card_draft": 0},  # en mazo, no descartable
        {"game_id": game_id, "type": "detective", "name": "detective_brent", "in_deck": 0, "in_card_draft": 0},  # en descartes
    ]
    await database.execute_many(deck_cards.insert(), dummy_cards)

    # 2. Crear manos dummy para los jugadores
    dummy_hand = [
        # Jugador 1
        {"game_id": game_id, "player_id": player1_id, "type": "Detective", "name": "detective_brent"},  # carta a descartar
        {"game_id": game_id, "player_id": player1_id, "type": "Detective", "name": "detective_oliver"},  # otra carta
        # Jugador 2
        {"game_id": game_id, "player_id": player2_id, "type": "Detective", "name": "detective_brent"},  # carta con mismo nombre que la a descartar
        {"game_id": game_id, "player_id": player2_id, "type": "Event", "name": "event_card_extra"},     # otra carta
    ]
    await database.execute_many(player_hands.insert(), dummy_hand)

    # 3. Ejecutar la función a testear para el jugador 1
    result = await card_services.discard_card(game_id, player1_id, card_name)

    # 4. Verificar respuesta
    assert result["success"] is True
    assert result["game_id"] == game_id
    assert result["discarded_card"] == card_name

    # 5. Verificar estado en deck_cards
    deck_cards_status = await database.fetch_all(
        """
        SELECT id, in_deck, in_card_draft FROM deck_cards
        WHERE game_id = :gid AND name = :cname
        """,
        {"gid": game_id, "cname": card_name}
    )
    assert len(deck_cards_status) == 6
    # 2 descartadas (in_deck=0, in_card_draft=0)
    discard_count = sum(1 for c in deck_cards_status if c["in_deck"] == 0 and c["in_card_draft"] == 0)
    assert discard_count == 2
    # La que no se descarto
    assert any(c["in_deck"] is None and c["in_card_draft"] == 0 for c in deck_cards_status)
    # Las otras deben permanecer sin cambios
    assert any(c["in_deck"] == 1 for c in deck_cards_status)  # en mazo
    assert any(c["in_card_draft"] == 1 for c in deck_cards_status)  # draft

    # 6. Verificar que la carta fue eliminada de la mano del jugador 1
    remaining_hand1 = await database.fetch_all(
        "SELECT id, name FROM player_hands WHERE game_id = :gid AND player_id = :pid",
        {"gid": game_id, "pid": player1_id}
    )
    assert all(c["name"] != card_name for c in remaining_hand1)
    assert any(c["name"] == "detective_oliver" for c in remaining_hand1)

    # 7. Verificar que la mano del jugador 2 no se modificó
    remaining_hand2 = await database.fetch_all(
        "SELECT id, name FROM player_hands WHERE game_id = :gid AND player_id = :pid",
        {"gid": game_id, "pid": player2_id}
    )
    assert any(c["name"] == card_name for c in remaining_hand2)
    assert any(c["name"] == "event_card_extra" for c in remaining_hand2)

    # 8. Limpiar datos dummy al final
    await database.execute("DELETE FROM deck_cards WHERE game_id = :gid", {"gid": game_id})
    await database.execute("DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id})
