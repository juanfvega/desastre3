from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.managers.connection_manager import connection_manager
from app.services.game_service import get_game, _build_lobby_state  # agregar import arriba
router = APIRouter()


@router.websocket("/games/{game_id}")
async def ws_game_endpoint(websocket: WebSocket, game_id: str):
    """
    Conexión WS por partida. Todos los mensajes relevantes (p.ej. turn_changed)
    serán broadcast por el ConnectionManager.
    """
    await connection_manager.connect(game_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(game_id, websocket)

@router.websocket("/ws/games/{game_id}")
async def websocket_games(websocket: WebSocket, game_id: str):
    # NOTE: signature is (game_id, websocket)
    await connection_manager.connect(game_id, websocket)
    game = await get_game(game_id)
    if game:
        # Construir snapshot de lobby y mandarlo solo a este cliente
        lobby_state = await _build_lobby_state(game)
        await websocket.send_json(lobby_state)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":  # ya lo tenés para tests
                await websocket.send_json({"type": "pong"})
            else:
                await connection_manager.broadcast_to_game(data, game_id)
    except WebSocketDisconnect:
        connection_manager.disconnect(game_id, websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        connection_manager.disconnect(game_id, websocket)


@router.websocket("/ws/games/")
async def websocket_games(websocket: WebSocket):  # global channel
    # Conectamos al WebSocket dentro del global (usamos game_id = "global")
    await connection_manager.connect("global", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping": #esto es solo para los test
                await websocket.send_json({"type": "pong"})
            else: #normalmente solo devuelve
                await connection_manager.broadcast_to_game(data, "global")

    except WebSocketDisconnect:
        # El cliente cerró la conexión
        connection_manager.disconnect("global", websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        connection_manager.disconnect("global", websocket)


@router.websocket("/ws/games/{game_id}")
async def websocket_game_player(websocket: WebSocket, game_id: str):
    """
    Conexión WS por partida. Solo acepta la conexión y la mantiene abierta.
    """
    await connection_manager.connect(game_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantiene la conexión abierta, ignora mensajes
    except WebSocketDisconnect:
        connection_manager.disconnect(game_id, websocket)
