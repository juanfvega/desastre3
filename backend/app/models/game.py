from datetime import datetime
from sqlalchemy import Boolean, Table, Column, String, Integer, Enum as SqlEnum, JSON, DateTime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import metadata

class GameStatus(str, Enum):
    WAITING = "waiting"
    PREPARATION = "preparation"
    PLAYING = "playing"
    FINISHED = "finished"
    
class TurnPhase (str, Enum):
    ACTION = "action"
    READY_TO_END = "ready_to_end"

class Action (str,Enum):
    NONE = "none"
    PLAYED = "played" #jugo una carta / set 
    DISCARD = "discard" #descarto manualmente 
    SKIP_ACTION = "skip_action" # no ejecuto accion

games = Table(
    "games",
    metadata,
    Column("id", String, primary_key=True),
    Column("nameGame", String, nullable=False),
    Column("num_players", Integer, nullable=False),
    Column("password", String, nullable=True),

    Column("status", SqlEnum(GameStatus), nullable=False, default=GameStatus.WAITING),
    Column("players", JSON, nullable=False, default=list),
    
    Column("host", String, nullable=True),
    Column("current_turn_player", String, nullable=True),
    Column("deck_initialized", Boolean, default=False),  # ✅ NUEVO

    Column("turn_phase", SqlEnum(TurnPhase), nullable= False, server_default= TurnPhase.ACTION),
    Column("last_action", SqlEnum(Action), nullable = False, server_default = Action.NONE),
)

# Clase Pydantic para mapear resultados de la DB
class Game(BaseModel):
    id: str
    nameGame: str
    num_players: int
    password: Optional[str] = None
    status: GameStatus
    host: str
    current_turn_player: Optional[str] = None
    players: List[str] = []
    
