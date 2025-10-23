import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import database
from app.services import game_service
from app.models.game import Game, GameStatus
from app.models.player import Player

client = TestClient(app)


@pytest.mark.asyncio
async def cleanup_test_data(*ids):
    """Función auxiliar para limpiar datos de prueba específicos"""
    for entity_id in ids:
        try:
            await game_service.delete_game(entity_id)
            await game_service.delete_player(entity_id)
        except:
            pass  # Ignore errors during cleanup


@pytest.mark.asyncio
async def setup_test_game_with_players_and_deck(
    game_id: str,
    host_id: str,
    additional_players: list = None,
    status: GameStatus = GameStatus.PREPARATION,
    num_players: int = 2
):
    """
    Helper para crear datos de prueba con juego y jugadores para tests de endpoints de cartas
    """
    await cleanup_test_data(game_id, host_id, *(additional_players or []))

    # Crear jugador host
    host_player = Player(
        id=host_id,
        username="Host Player",
        birthdate=date(1990, 9, 15).isoformat(),
        avatar=None,
        at_game=game_id
    )
    await game_service.save_player(host_player)

    # Crear jugadores adicionales
    players_list = [host_id]
    for i, pid in enumerate(additional_players or []):
        player = Player(
            id=pid,
            username=f"Player {i+1}",
            birthdate=date(1995, 1, 1).isoformat(),
            avatar=None,
            at_game=game_id
        )
        await game_service.save_player(player)
        players_list.append(pid)

    # Crear partida
    game = Game(
        id=game_id,
        nameGame="Test Game",
        host=host_id,
        status=status.value,
        num_players=num_players,
        players=players_list,
        current_turn_player=None,
        password=None,
    )
    await game_service.save_game(game)
    
    # Crear cartas en el deck para el test
    deck_query = """
    INSERT INTO deck_cards (game_id, type, name, in_deck, in_card_draft)
    VALUES (:game_id, :type, :name, :in_deck, :in_card_draft)
    """
    # Crear suficientes cartas para el test (6 cartas por jugador = 12 cartas mínimo)
    # También necesitamos cartas especiales "Not so fast" (una por jugador)
    cards_to_create = [
        # Cartas especiales "Not so fast" (una por jugador)
        {"game_id": game_id, "type": "not_so_fast", "name": "Not so fast", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "not_so_fast", "name": "Not so fast", "in_deck": True, "in_card_draft": False},
        # Cartas normales
        {"game_id": game_id, "type": "detective", "name": "Card 1", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 2", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 3", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 4", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 5", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 6", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 7", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 8", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 9", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 10", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 11", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 12", "in_deck": True, "in_card_draft": False},
    ]
    
    await database.execute_many(deck_query, cards_to_create)
    
    return game_id, players_list


# ============================================================================
# Tests para endpoints de cartas
# ============================================================================

@pytest.mark.asyncio
async def test_deal_cards_round_robin_service():
    """
    Verifica que el endpoint /games/{game_id}/deal reparta las cartas correctamente
    cuando el juego está en estado PLAYING.
    """
    game_id = "test-deal-endpoint-game"
    host_id = "host-deal-endpoint"
    player2_id = "player2-deal-endpoint"

    game_id, _ = await setup_test_game_with_players_and_deck(
        game_id, host_id, [player2_id], num_players=2
    )

    response = client.post(f"/games/{game_id}/deal")
    assert response.status_code == 200

    data = response.json()
    assert "summary" in data
    assert isinstance(data["summary"], list)

    # Cleanup
    await cleanup_test_data(game_id, host_id, player2_id)


@pytest.mark.asyncio
async def test_get_player_cards_endpoint():
    """
    Inserta algunas cartas en la mano de un jugador y valida que
    el endpoint /player/cards/{player_id} las devuelva.
    """
    game_id = "test-player-cards-game"
    host_id = "host-player-cards"
    player2_id = "player2-player-cards"

    _, player_ids = await setup_test_game_with_players_and_deck(
        game_id, host_id, [player2_id], num_players=2
    )
    player_id = player_ids[0]

    # Insertamos cartas manualmente en la mano del jugador
    query = """
    INSERT INTO player_hands (game_id, player_id, type, name)
    VALUES (:game_id, :player_id, :type, :name)
    """
    await database.execute_many(query=query, values=[
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "Test Card 1"},
        {"game_id": game_id, "player_id": player_id, "type": "detective", "name": "Test Card 2"},
    ])

    response = client.get(f"/games/player/cards/{player_id}")
    assert response.status_code == 200

    cards = response.json()
    assert any(card["name"] == "Test Card 1" for card in cards)
    assert any(card["name"] == "Test Card 2" for card in cards)

    # Cleanup
    await cleanup_test_data(game_id, host_id, player2_id)
