import pytest
import pytest_asyncio
from sqlalchemy import text
from fastapi.testclient import TestClient
from app.core.database import database
from app.main import app
from app.services import game_service, card_services
from app.models.game import GameStatus

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Set up and tear down test database for each test."""
    # Connect to database
    if not database.is_connected:
        await database.connect()
    
    # Create tables using raw SQL
    await database.execute(text("""
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            nameGame TEXT NOT NULL,
            num_players INTEGER NOT NULL,
            password TEXT,
            status TEXT NOT NULL DEFAULT 'waiting',
            host TEXT NOT NULL,
            current_turn_player TEXT,
            players TEXT NOT NULL DEFAULT '[]'
        )
    """))
    
    await database.execute(text("""
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            birthdate TEXT,
            avatar TEXT,
            at_game TEXT REFERENCES games(id)
        )
    """))
    
    await database.execute(text("""
        CREATE TABLE IF NOT EXISTS deck_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL REFERENCES games(id),
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            in_deck BOOLEAN DEFAULT TRUE,
            in_card_draft BOOLEAN DEFAULT FALSE
        )
    """))
    
    await database.execute(text("""
        CREATE TABLE IF NOT EXISTS player_hands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL REFERENCES games(id),
            player_id TEXT NOT NULL REFERENCES players(id),
            type TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """))

    yield
    
    # Clean up: drop all tables
    await database.execute(text("DROP TABLE IF EXISTS player_hands"))
    await database.execute(text("DROP TABLE IF EXISTS deck_cards"))
    await database.execute(text("DROP TABLE IF EXISTS players"))
    await database.execute(text("DROP TABLE IF EXISTS games"))

@pytest_asyncio.fixture
async def setup_game_with_players_and_deck():
    # Crear un juego en estado PLAYING
    game = await game_service.create_game("Test Game")
    await game_service.update_game_status(game["id"], GameStatus.PLAYING)

    # Crear jugadores
    player1 = await game_service.add_player(game["id"], "Alice")
    player2 = await game_service.add_player(game["id"], "Bob")

    return game["id"], [player1["id"], player2["id"]]

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
