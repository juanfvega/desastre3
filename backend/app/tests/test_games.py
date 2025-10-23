import pytest
import random
from fastapi.testclient import TestClient
from datetime import date
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.game import Game, GameStatus
from app.models.player import Player
from app.services import game_service
from app.services.game_service import BASE_CARDS

client = TestClient(app)

def create_mock_cards(count: int):
    """Helper para crear cartas mock realistas basadas en BASE_CARDS"""
    cards = []
    for i in range(count):
        card_template = random.choice(BASE_CARDS)
        cards.append({
            "id": f"card-{i}",
            "type": card_template["type"],
            "name": card_template["name"]
        })
    return cards


# ============================================================================
# Tests para endpoint POST /api/games/{game_id}/start
# ============================================================================

@pytest.mark.asyncio
async def test_start_game_success():
    """Caso feliz: el host inicia correctamente un juego"""
    game_id = "test-start-success"
    host_id = "host-player-123"
    player2_id = "player2-789"

    # Mock del juego antes de iniciar
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=2,
        players=[host_id, player2_id],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.services.game_service.save_game", new_callable=AsyncMock) as mock_save_game, \
         patch("app.managers.connection_manager.manager.broadcast_to_game", new_callable=AsyncMock) as mock_broadcast, \
         patch("app.services.game_service._determine_first_player", new_callable=AsyncMock) as mock_first_player, \
         patch("app.services.card_services.initialize_deck", new_callable=AsyncMock) as mock_init_deck, \
         patch("app.services.card_services.deal_cards_round_robin", new_callable=AsyncMock) as mock_deal_cards:

        mock_get_game.return_value = mock_game
        mock_first_player.return_value = host_id
        mock_init_deck.return_value = None 
        mock_deal_cards.return_value = None

        response = client.post(f"/api/games/{game_id}/start", json={"player_id": host_id})

        # --- Verificaciones HTTP ---
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["game_id"] == game_id

        # --- Verificar que se llamaron los servicios en orden correcto ---
        mock_first_player.assert_awaited_once_with(mock_game)
        await mock_deal_cards(game_id, mock_game.players)
        mock_deal_cards.assert_awaited_once_with(game_id, mock_game.players)
        mock_save_game.assert_awaited()

        # --- Verificar que se guardó el juego con estado actualizado ---
        assert mock_save_game.await_args is not None
        saved_game = mock_save_game.await_args.args[0]
        assert saved_game.status == GameStatus.PREPARATION.value
        assert saved_game.current_turn_player == host_id

        # --- Verificar que se envió el broadcast ---
        mock_broadcast.assert_awaited()

@pytest.mark.asyncio
async def test_start_game_insufficient_players():
    """Debe fallar si no hay suficientes jugadores para iniciar"""
    game_id = "test-insufficient-players"
    host_id = "host-alone"

    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=2,
        players=[host_id],  # solo uno
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = mock_game

        response = client.post(f"/api/games/{game_id}/start", json={"player_id": host_id})
        assert response.status_code == 400
        assert "insufficient players" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_game_not_owner():
    """Debe fallar si quien inicia no es el host"""
    game_id = "test-ownership-validation"
    host_id = "real-host"
    fake_host_id = "fake-host"

    mock_game = Game(
        id=game_id,
        nameGame="Ownership Test Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=2,
        players=[host_id, fake_host_id],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = mock_game

        response = client.post(f"/api/games/{game_id}/start", json={"player_id": fake_host_id})
        assert response.status_code == 403
        assert "only the host" in response.json()["detail"].lower()


def test_start_game_not_found():
    """Debe fallar si el juego no existe"""
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = None

        response = client.post("/api/games/nonexistent-game-id/start", json={"player_id": "any-player"})
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_game_already_started():
    """No se puede iniciar un juego que ya está en PLAYING"""
    game_id = "test-already-started"
    host_id = "host-started"

    mock_game = Game(
        id=game_id,
        nameGame="Already Started Game",
        host=host_id,
        status=GameStatus.PLAYING.value,
        num_players=2,
        players=[host_id, "player2"],
        current_turn_player=host_id,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = mock_game

        response = client.post(f"/api/games/{game_id}/start", json={"player_id": host_id})
        assert response.status_code == 409
        assert "game is in state" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_game_turn_assignment_closest_birthday():
    """Verifica que el jugador con cumpleaños más cercano a Agatha Christie empiece"""
    game_id = "test-birthday-logic"
    host_id = "host-far-birthday"
    close_birthday_player = "player-close-birthday"

    # Creamos el mock del juego
    mock_game = Game(
        id=game_id,
        nameGame="Birthday Test Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=2,
        players=[host_id, close_birthday_player],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    # Simulamos que el jugador con cumpleaños más cercano es "close_birthday_player"
    expected_first = close_birthday_player

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.services.game_service._determine_first_player", new_callable=AsyncMock) as mock_first_player, \
         patch("app.services.card_services.initialize_deck", new_callable=AsyncMock) as mock_init_deck, \
         patch("app.services.card_services.deal_cards_round_robin", new_callable=AsyncMock) as mock_deal_cards, \
         patch("app.services.game_service.save_game", new_callable=AsyncMock) as mock_save_game, \
         patch("app.managers.connection_manager.manager.broadcast_to_game", new_callable=AsyncMock) as mock_broadcast:

        # Configuramos los mocks
        mock_get_game.return_value = mock_game
        mock_first_player.return_value = expected_first
        mock_init_deck.return_value = None  
        mock_deal_cards.return_value = None 

        response = client.post(f"/api/games/{game_id}/start", json={"player_id": host_id})

        # --- Verificaciones HTTP ---
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # --- Verificar que el método se llamó correctamente ---
        mock_first_player.assert_awaited_once_with(mock_game)

        # --- Verificar que se guardó el juego con el jugador correcto ---
        assert mock_save_game.await_args is not None
        saved_game = mock_save_game.await_args.args[0]
        assert saved_game.current_turn_player == expected_first, \
            f"El turno inicial debería asignarse a {expected_first}, pero fue {saved_game.current_turn_player}"

        # --- Verificar que el broadcast se envió ---
        mock_broadcast.assert_awaited()


# ============================================================================
# Tests para endpoint POST /api/games/{game_id}/join
# ============================================================================

@pytest.mark.asyncio
async def test_join_game_success():
    """Un jugador válido se une correctamente al juego"""
    game_id = "test-join-success"
    host_id = "host-player-join"
    joiner_id = "new-joiner-player"

    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=4,
        players=[host_id],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    updated_game = Game(
        id=game_id,
        nameGame="Test Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=4,
        players=[host_id, joiner_id],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.services.game_service.get_player", new_callable=AsyncMock) as mock_get_player, \
         patch("app.services.game_service.join_game", new_callable=AsyncMock) as mock_join_game, \
         patch("app.managers.connection_manager.manager.broadcast_to_game", new_callable=AsyncMock):

        mock_get_game.return_value = mock_game
        mock_get_player.return_value = Player(id=joiner_id, username="Joiner")
        mock_join_game.return_value = updated_game

        response = client.post(f"/api/games/{game_id}/join", json={"player_id": joiner_id})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["game_id"] == game_id
        assert data["players_count"] == 2

        mock_join_game.assert_awaited()


@pytest.mark.asyncio
async def test_join_game_not_found():
    """Error si el juego no existe"""
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = None
        response = client.post("/api/games/nonexistent-game-id/join", json={"player_id": "any-player"})
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_join_game_player_not_found():
    """Error si el jugador no existe"""
    game_id = "test-join-player-not-found"
    host_id = "host-player-not-found"

    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=3,
        players=[host_id],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.services.game_service.get_player", new_callable=AsyncMock) as mock_get_player:

        mock_get_game.return_value = mock_game
        mock_get_player.return_value = None

        response = client.post(f"/api/games/{game_id}/join", json={"player_id": "nonexistent-player-id"})
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_join_game_full():
    """No se puede unir si el juego ya está lleno"""
    game_id = "test-join-full"
    host_id = "host-full-game"
    rejected_player = "rejected-player"

    mock_game = Game(
        id=game_id,
        nameGame="Full Game",
        host=host_id,
        status=GameStatus.WAITING.value,
        num_players=2,
        players=[host_id, "existing-player"],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.services.game_service.get_player", new_callable=AsyncMock) as mock_get_player:
        
        mock_get_game.return_value = mock_game
        mock_get_player.return_value = Player(id=rejected_player, username="Rejected Player")

        response = client.post(f"/api/games/{game_id}/join", json={"player_id": rejected_player})
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_join_game_in_progress():
    """No se puede unir a un juego en progreso"""
    game_id = "test-join-in-progress"
    host_id = "host-in-progress"

    mock_game = Game(
        id=game_id,
        nameGame="In Progress Game",
        host=host_id,
        status=GameStatus.PLAYING.value,
        num_players=3,
        players=[host_id, "p1"],
        current_turn_player=host_id,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.services.game_service.get_player", new_callable=AsyncMock) as mock_get_player:
        
        mock_get_game.return_value = mock_game
        mock_get_player.return_value = Player(id="new-player", username="New Player")

        response = client.post(f"/api/games/{game_id}/join", json={"player_id": "new-player"})
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_join_game_finished():
    """No se puede unir a un juego finalizado"""
    game_id = "test-join-finished"
    host_id = "host-finished"

    mock_game = Game(
        id=game_id,
        nameGame="Finished Game",
        host=host_id,
        status=GameStatus.FINISHED.value,
        num_players=3,
        players=[host_id, "p1"],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )

    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.services.game_service.get_player", new_callable=AsyncMock) as mock_get_player:
        
        mock_get_game.return_value = mock_game
        mock_get_player.return_value = Player(id="new-player", username="New Player")

        response = client.post(f"/api/games/{game_id}/join", json={"player_id": "new-player"})
        assert response.status_code == 409


# ============================================================================
# Tests para endpoint POST /api/games/{game_id}/players/{player_id}/draw
# ============================================================================

@pytest.mark.asyncio
async def test_draw_cards_success():
    """Test: Jugador roba cartas exitosamente para completar su mano"""
    game_id = "test-draw-success"
    player_id = "player-123"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.PLAYING.value,
        num_players=2,
        players=["host-123", player_id],
        current_turn_player=player_id,
        password=None,
        deck_initialized=True,
    )
    
    mock_drawn_cards = create_mock_cards(3)
    
    # Mock de cartas disponibles en el mazo (más de las necesarias)
    mock_remaining_cards = [
        {"id": f"deck-card-{i}", "type": "action", "name": "Test Card", "in_deck": 1}
        for i in range(10)
    ]
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.core.database.database.fetch_val", new_callable=AsyncMock) as mock_fetch_val, \
         patch("app.core.database.database.fetch_all", new_callable=AsyncMock) as mock_fetch_all, \
         patch("app.services.card_services.draw_cards", new_callable=AsyncMock) as mock_draw:
        
        mock_get_game.return_value = mock_game
        mock_fetch_val.return_value = 3  # Tiene 3 cartas en mano
        mock_fetch_all.return_value = mock_remaining_cards  # 10 cartas disponibles
        mock_draw.return_value = mock_drawn_cards
        
        response = client.post(f"/api/games/{game_id}/players/{player_id}/draw")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cards drawn successfully"
        assert "cards" in data
        assert len(data["cards"]) == 3
        assert "remaining_in_deck" in data
        assert data["remaining_in_deck"] == 7  # 10 - 3
        
        # Verificar que se llamó a draw_cards con los parámetros correctos
        mock_draw.assert_called_once_with(game_id, player_id, 3)


@pytest.mark.asyncio
async def test_draw_cards_empty_hand():
    """Test: Jugador roba cartas con mano vacía (debe robar 6)"""
    game_id = "test-draw-empty"
    player_id = "player-empty"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.PLAYING.value,
        num_players=2,
        players=["host-123", player_id],
        current_turn_player=player_id,
        password=None,
        deck_initialized=True,
    )
    
    mock_drawn_cards = create_mock_cards(6)
    
    # Mock de cartas disponibles en el mazo
    mock_remaining_cards = [
        {"id": f"deck-card-{i}", "type": "action", "name": "Test Card", "in_deck": 1}
        for i in range(15)
    ]
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.core.database.database.fetch_val", new_callable=AsyncMock) as mock_fetch_val, \
         patch("app.core.database.database.fetch_all", new_callable=AsyncMock) as mock_fetch_all, \
         patch("app.services.card_services.draw_cards", new_callable=AsyncMock) as mock_draw:
        
        mock_get_game.return_value = mock_game
        mock_fetch_val.return_value = 0  # Mano vacía
        mock_fetch_all.return_value = mock_remaining_cards  # 15 cartas disponibles
        mock_draw.return_value = mock_drawn_cards
        
        response = client.post(f"/api/games/{game_id}/players/{player_id}/draw")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cards drawn successfully"
        assert len(data["cards"]) == 6
        assert data["remaining_in_deck"] == 9  # 15 - 6
        
        mock_draw.assert_called_once_with(game_id, player_id, 6)


@pytest.mark.asyncio
async def test_draw_cards_hand_full():
    """Test: Jugador con mano completa no debe robar cartas"""
    game_id = "test-draw-full"
    player_id = "player-full"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.PLAYING.value,
        num_players=2,
        players=["host-123", player_id],
        current_turn_player=player_id,
        password=None,
        deck_initialized=True,
    )
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.core.database.database.fetch_val", new_callable=AsyncMock) as mock_fetch_val:
        
        mock_get_game.return_value = mock_game
        mock_fetch_val.return_value = 6  # Mano completa
        
        response = client.post(f"/api/games/{game_id}/players/{player_id}/draw")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "No cards to draw"
        assert "cards" not in data


@pytest.mark.asyncio
async def test_draw_cards_game_not_found():
    """Test: Error cuando el juego no existe"""
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = None
        
        response = client.post("/api/games/nonexistent-game/players/some-player/draw")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_draw_cards_game_not_playing():
    """Test: Error cuando el juego no está en estado PLAYING"""
    game_id = "test-draw-waiting"
    player_id = "player-waiting"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.WAITING.value,
        num_players=2,
        players=["host-123", player_id],
        current_turn_player=None,
        password=None,
        deck_initialized=False,
    )
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = mock_game
        
        response = client.post(f"/api/games/{game_id}/players/{player_id}/draw")
        
        assert response.status_code == 400
        data = response.json()
        assert "must be in playing state" in data["detail"].lower() or "playing" in data["detail"].lower()


@pytest.mark.asyncio
async def test_draw_cards_not_your_turn():
    """Test: Error cuando no es el turno del jugador"""
    game_id = "test-draw-wrong-turn"
    current_player_id = "player-with-turn"
    other_player_id = "player-without-turn"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.PLAYING.value,
        num_players=2,
        players=["host-123", current_player_id, other_player_id],
        current_turn_player=current_player_id,
        password=None,
        deck_initialized=True,
    )
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = mock_game
        
        # Intentar robar con un jugador que NO tiene el turno
        response = client.post(f"/api/games/{game_id}/players/{other_player_id}/draw")
        
        assert response.status_code == 403
        data = response.json()
        assert "not your turn" in data["detail"].lower() or "turn" in data["detail"].lower()


@pytest.mark.asyncio
async def test_draw_cards_no_cards_in_deck():
    """Test: Cuando no hay cartas disponibles en el mazo (pero draw_cards devuelve vacío)"""
    game_id = "test-draw-empty-deck"
    player_id = "player-empty-deck"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.PLAYING.value,
        num_players=2,
        players=["host-123", player_id],
        current_turn_player=player_id,
        password=None,
        deck_initialized=True,
    )
    
    # Mock de cartas disponibles en el mazo (suficientes)
    mock_remaining_cards = [
        {"id": f"deck-card-{i}", "type": "action", "name": "Test Card", "in_deck": 1}
        for i in range(10)
    ]
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.core.database.database.fetch_val", new_callable=AsyncMock) as mock_fetch_val, \
         patch("app.core.database.database.fetch_all", new_callable=AsyncMock) as mock_fetch_all, \
         patch("app.services.card_services.draw_cards", new_callable=AsyncMock) as mock_draw:
        
        mock_get_game.return_value = mock_game
        mock_fetch_val.return_value = 2  # Tiene 2 cartas, necesita 4
        mock_fetch_all.return_value = mock_remaining_cards
        mock_draw.return_value = []  # draw_cards falla y devuelve vacío
        
        response = client.post(f"/api/games/{game_id}/players/{player_id}/draw")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "No cards left in the deck"


@pytest.mark.asyncio
async def test_draw_cards_game_finished():
    """Test: Error cuando el juego está terminado"""
    game_id = "test-draw-finished"
    player_id = "player-finished"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.FINISHED.value,
        num_players=2,
        players=["host-123", player_id],
        current_turn_player=player_id,
        password=None,
        deck_initialized=True,
    )
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game:
        mock_get_game.return_value = mock_game
        
        response = client.post(f"/api/games/{game_id}/players/{player_id}/draw")
        
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_draw_cards_game_ends_when_deck_exhausted():
    """Test: El juego termina cuando se agotan las cartas del mazo al robar"""
    game_id = "test-draw-game-ends"
    player_id = "player-ends-game"
    
    mock_game = Game(
        id=game_id,
        nameGame="Test Game",
        host="host-123",
        status=GameStatus.PLAYING.value,
        num_players=2,
        players=["host-123", player_id],
        current_turn_player=player_id,
        password=None,
        deck_initialized=True,
    )
    
    # Mock: solo quedan 2 cartas en el mazo, pero el jugador necesita 4
    mock_remaining_cards = [
        {"id": "last-card-1", "type": "action", "name": "Card 1", "in_deck": 1},
        {"id": "last-card-2", "type": "action", "name": "Card 2", "in_deck": 1},
    ]
    
    with patch("app.services.game_service.get_game", new_callable=AsyncMock) as mock_get_game, \
         patch("app.core.database.database.fetch_val", new_callable=AsyncMock) as mock_fetch_val, \
         patch("app.core.database.database.fetch_all", new_callable=AsyncMock) as mock_fetch_all, \
         patch("app.core.database.database.execute", new_callable=AsyncMock) as mock_execute, \
         patch("app.managers.connection_manager.manager.broadcast_to_game", new_callable=AsyncMock) as mock_broadcast:
        
        mock_get_game.return_value = mock_game
        mock_fetch_val.return_value = 2  # Tiene 2 cartas, necesita 4
        mock_fetch_all.return_value = mock_remaining_cards  # Solo 2 disponibles
        
        response = client.post(f"/api/games/{game_id}/players/{player_id}/draw")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que el juego terminó
        assert data["message"] == "Game finished! Murderer escapes!"
        assert data["winner"] == player_id
        assert "winner" in data
        
        # Verificar que se actualizó el estado del juego a FINISHED
        # (se llama execute 3 veces: insert cartas, delete del mazo, update game status)
        assert mock_execute.call_count >= 3
        
        # Verificar que se envió el broadcast
        mock_broadcast.assert_awaited_once()
        broadcast_call = mock_broadcast.call_args[0][0]
        assert broadcast_call["event"] == "game_end"
        assert broadcast_call["game_id"] == game_id
        assert broadcast_call["winner"] == player_id