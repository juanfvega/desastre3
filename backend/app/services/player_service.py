from __future__ import annotations
import uuid
from typing import Optional
from app.models.player import players_table, Player
from app.managers.game_manager import game_manager
from app.core.database import database

async def create_or_update_player(username: str, birthdate: str = None, avatar: str = None):
    if not username or not username.strip():
        raise ValueError("Username is required and cannot be empty")
    #eso ya lo hacia en otro lado pero bueno ok, lo dejo 
    
    print(f"Checking if player exists: username={username}")
    query = players_table.select().where(players_table.c.username == username)
    existing = await database.fetch_one(query)

    if existing:
        update_query = players_table.update().where(players_table.c.username == username)
        update_values = {}
        if birthdate is not None:
            update_values["birthdate"] = birthdate
        if update_values:
            await database.execute(update_query.values(**update_values))
        return dict(existing)

    # Nuevo jugador: permitimos crear aunque falte birthdate o avatar (pueden completarse luego)
    
    # Sorry, no puedo permitir la fecha si el jugador es 100% nuevo, el avatar si porque simplemente 
    # le ponia algo por defecto pero la fecha no es posible, romperia muchas cosas
    
    print("Creating new player")
    if not birthdate:
        raise ValueError("Obligatorio poner fecha si el usuario es nuevo")

    new_id = str(uuid.uuid4())
    insert_query = players_table.insert().values(
        id=new_id, username=username, birthdate=birthdate, avatar=avatar
    )
    await database.execute(insert_query)
    return {"id": new_id, "username": username, "birthdate": birthdate, "avatar": avatar}

class PlayerService:
    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """
        Busca el jugador en todas las partidas en memoria.
        Devuelve Player o None si no existe.
        """
        for game in game_manager.games.values():
            for p in getattr(game, "players", []) or []:
                if getattr(p, "id", None) == player_id:
                    return p
        return None

player_service = PlayerService()