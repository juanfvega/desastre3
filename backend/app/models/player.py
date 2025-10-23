from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Table, Column, String, ForeignKey
from app.core.database import metadata

players_table = Table(
    "players",
    metadata,
    Column("id", String, primary_key=True),
    Column("username", String, unique=True, nullable=False),
    Column("birthdate", String, nullable=True),
    Column("avatar", String, nullable=True),
    Column("at_game", String, ForeignKey("games.id"), nullable=True),
)

class Player(BaseModel):
    id: str
    username: str
    birthdate: Optional[str] = None
    avatar: Optional[str] = None
    at_game: Optional[str] = None

