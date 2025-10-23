import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_player():
    payload = {
        "username": "pepe_test",
        "birthdate": "2000-01-01",
        "avatar": "avatar.png"
    }
    response = client.post("/api/players", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "pepe_test"
    assert data["birthdate"] == "2000-01-01"
    assert data["avatar"] == "avatar.png"


def test_create_game():
    payload = {
        "nameGame": "PartidaTest",
        "num_players": 4,
        "password": None
    }
    response = client.post("/api/games", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nameGame"] == "PartidaTest"
    assert data["num_players"] == 4
    assert data["status"] == "waiting"


def test_websocket_game_id():
    with client.websocket_connect("/api/ws/games/test-game-id") as websocket:
        # Enviamos JSON
        websocket.send_json({"type": "ping"})
        # Recibimos JSON
        data = websocket.receive_json()
        assert data == {"type": "pong"}  # debe coincidir con lo que envía el servidor

def test_websocket_game():
    with client.websocket_connect("/api/ws/games/") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data == {"type": "pong"}
