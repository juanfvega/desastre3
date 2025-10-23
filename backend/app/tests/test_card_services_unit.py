import pytest
from datetime import date
from app.services import card_services, game_service
from app.core.database import database
from app.models.game import Game, GameStatus
from app.models.player import Player


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
    Helper para crear datos de prueba con juego y jugadores para tests de cartas
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
    # Crear suficientes cartas para el test (6 visibles + 3 secretas por jugador = 18 cartas mínimo)
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
        {"game_id": game_id, "type": "detective", "name": "Card 13", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 14", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 15", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 16", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 17", "in_deck": True, "in_card_draft": False},
        {"game_id": game_id, "type": "detective", "name": "Card 18", "in_deck": True, "in_card_draft": False},
    ]
    
    await database.execute_many(deck_query, cards_to_create)
    
    return game_id, players_list


# ============================================================================
# Tests para servicios de cartas
# ============================================================================

@pytest.mark.asyncio
async def test_deal_cards_round_robin_function():
    """
    Verifica directamente la función deal_cards_round_robin del servicio.
    Comprueba que reparte las cartas correctas a cada jugador.
    """
    game_id = "test-deal-cards-game"
    host_id = "host-deal-cards"
    player2_id = "player2-deal-cards"

    game_id, player_ids = await setup_test_game_with_players_and_deck(
        game_id, host_id, [player2_id], num_players=2
    )

    # Ejecutar la lógica de repartir cartas
    await card_services.deal_cards_round_robin(game_id)

    # Consultar cartas de los jugadores
    query = "SELECT player_id, type, name FROM player_hands WHERE game_id = :game_id"
    rows = await database.fetch_all(query, values={"game_id": game_id})

    assert rows, "Los jugadores deberían tener cartas repartidas"

    # Validar que cada jugador tenga cartas
    players_with_cards = {row["player_id"] for row in rows}
    for pid in player_ids:
        assert pid in players_with_cards

    # Validar que la cantidad de cartas coincida con lo esperado (6 cartas por jugador)
    cards_per_player = {}
    for row in rows:
        cards_per_player.setdefault(row["player_id"], []).append(row)

    for pid, cards in cards_per_player.items():
        assert len(cards) == card_services.REQUIRED_CARDS
        
    # Verificar que cada jugador tiene exactamente una carta "Not so fast"
    for pid, cards in cards_per_player.items():
        not_so_fast_cards = [c for c in cards if c["name"] == "Not so fast"]
        assert len(not_so_fast_cards) == 1, f"Player {pid} should have exactly one 'Not so fast' card"

    # Cleanup
    await cleanup_test_data(game_id, host_id, player2_id)
