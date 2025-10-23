import pytest
import time
from starlette.testclient import TestClient
from asgi_lifespan import LifespanManager
from app.main import app


def test_watch_set_with_websocket():
    """
    STORY P0.4 - Ver Sets (con WebSocket)
    Versión final compatible con el formato real del backend:
    {
      "data": {...},
      "event": "lobby_state",
      "gameId": "..."
    }
    """

    import asyncio
    loop = asyncio.get_event_loop()

    async def run_flow():
        async with LifespanManager(app):
            client = TestClient(app)

            # Crear jugadores
            p1 = client.post("/api/players", json={
                "username": "Hercule Poirot",
                "birthdate": "1970-05-05"
            }).json()["id"]
            p2 = client.post("/api/players", json={
                "username": "Miss Marple",
                "birthdate": "1960-08-21"
            }).json()["id"]
            p3 = client.post("/api/players", json={
                "username": "Tommy",
                "birthdate": "1985-02-10"
            }).json()["id"]

            # Crear partida
            game = client.post("/api/games", json={
                "nameGame": "Mansion WS Test",
                "num_players": 3,
                "player_id": p1
            }).json()
            game_id = game["id"]

            # Unir jugadores
            client.post(f"/api/games/{game_id}/join", json={"player_id": p2})
            client.post(f"/api/games/{game_id}/join", json={"player_id": p3})

            # Iniciar partida
            start = client.post(f"/api/games/{game_id}/start", json={"player_id": p1})
            assert start.status_code == 200

            # Asignar secretos
            secrets = client.post(f"/api/games/{game_id}/deal_secrets")
            assert secrets.status_code == 200
            assert secrets.json()["success"]

            # Conectarse al WebSocket del juego
            with client.websocket_connect(f"/ws/games/{game_id}") as ws:
                initial_event = ws.receive_json()
                # Validar que el WS manda el evento esperado
                assert "event" in initial_event
                assert initial_event["event"] == "lobby_state"
                assert "data" in initial_event
                data = initial_event["data"]
                assert "players" in data
                assert len(data["players"]) == 3
                assert data["status"] in ("preparation", "playing")

                # Llamar al endpoint /watch_set 
                response = client.get(f"/api/games/{game_id}/watch_set")
                assert response.status_code == 200
                payload = response.json()
                assert "sets" in payload
                assert len(payload["sets"]) == 3

                # Validar estructura de un set
                one_player = payload["sets"][0]
                assert "player_id" in one_player
                assert "player_name" in one_player
                assert isinstance(one_player["sets"], list)
                inner = one_player["sets"][0]
                assert "detective" in inner
                assert "cards_count" in inner
                assert "has_harley_quinn" in inner
                assert "revealed" in inner

    loop.run_until_complete(run_flow())
