from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Diccionario con game_id -> lista de WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.player_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        """Acepta un WebSocket y lo añade al juego correspondiente"""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket):
        """Elimina un WebSocket de un juego"""
        if game_id in self.active_connections:
            self.active_connections[game_id].remove(websocket)
            if len(self.active_connections[game_id]) == 0:
                del self.active_connections[game_id]
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Envía un mensaje solo a un WebSocket"""
        await websocket.send_json(message)

    async def broadcast_to_game(self, message: dict, game_id: str):
        """Envía un mensaje a todos los WebSockets de un juego"""
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message to connection: {e}")


# Instancia global
connection_manager = ConnectionManager()
manager = connection_manager
managers = connection_manager

__all__ = ["ConnectionManager", "connection_manager", "manager", "managers"]
