import pytest
from asgi_lifespan import LifespanManager
from starlette.testclient import TestClient
from app.main import app


def test_watch_set_flow():
    """
    STORY P0.4 - Ver Sets
    Flujo completo: crear partida, registrar jugadores, unirlos, asignar secretos y obtener sets.
    Incluye campo obligatorio 'birthdate' para creación de jugadores.
    """

    import asyncio
    loop = asyncio.get_event_loop()

    async def run_flow():
        async with LifespanManager(app):  # inicia y finaliza correctamente la app
            client = TestClient(app)

            # Crear jugadores 
            player1 = client.post("/api/players", json={
                "username": "Hercule Poirot",
                "birthdate": "1970-05-05"
            })
            player2 = client.post("/api/players", json={
                "username": "Miss Marple",
                "birthdate": "1960-08-21"
            })
            player3 = client.post("/api/players", json={
                "username": "Tommy",
                "birthdate": "1985-02-10"
            })

            assert player1.status_code in (200, 201)
            assert player2.status_code in (200, 201)
            assert player3.status_code in (200, 201)

            p1 = player1.json()["id"]
            p2 = player2.json()["id"]
            p3 = player3.json()["id"]

            # Crear partida 
            create_game = client.post("/api/games", json={
                "nameGame": "Mystery Mansion",
                "num_players": 3,
                "player_id": p1
            })
            assert create_game.status_code in (200, 201)
            game_id = create_game.json()["id"]

            # Unir jugadores 
            join1 = client.post(f"/api/games/{game_id}/join", json={"player_id": p2})
            join2 = client.post(f"/api/games/{game_id}/join", json={"player_id": p3})
            assert join1.status_code == 200
            assert join2.status_code == 200

            # Iniciar partida 
            start = client.post(f"/api/games/{game_id}/start", json={"player_id": p1})
            assert start.status_code == 200
            assert start.json()["success"]

            # Asignar secretos (sets visibles) 
            secrets = client.post(f"/api/games/{game_id}/deal_secrets")
            assert secrets.status_code == 200
            data = secrets.json()
            assert data["success"] is True
            assert "assigned" in data

            # Consultar los sets visibles 
            watch = client.get(f"/api/games/{game_id}/watch_set")
            assert watch.status_code == 200

            result = watch.json()
            assert "sets" in result
            assert result["game_id"] == game_id
            assert isinstance(result["sets"], list)
            assert len(result["sets"]) == 3  # tres jugadores

            # Validar estructura interna
            for s in result["sets"]:
                assert "player_id" in s
                assert "player_name" in s
                assert isinstance(s["sets"], list)
                assert len(s["sets"]) >= 1
                inner = s["sets"][0]
                assert "detective" in inner
                assert "cards_count" in inner
                assert "has_harley_quinn" in inner
                assert "revealed" in inner

    loop.run_until_complete(run_flow())
