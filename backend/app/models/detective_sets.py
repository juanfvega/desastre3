from sqlalchemy import JSON, Table, Column, String, Integer, ForeignKey
from app.core.database import metadata

detective_sets = Table(
    "detective_sets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("game_id", String, ForeignKey("games.id"), nullable=False),
    Column("player_id", String, ForeignKey("players.id"), nullable=False),
    Column("detective_name", String, nullable=False),  # nombre base del conjunto
    Column("set_size", Integer, nullable=False),  # cantidad de cartas en el set
    Column("cards_used", JSON, nullable=False, default=list) # lista de los nombres de las cartas usadas en el set
)