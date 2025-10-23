from sqlalchemy import Table, Column, Integer, String, ForeignKey
from app.core.database import metadata

# Mano del jugador (cartas DOTC)
# type: detective | event | devious | not_so_fast | murderer_escapes (etc.)
# name: nombre de la carta (ej. "Hercule Poirot", "Not so Fast...", "Dead Card Folly")
player_hands = Table(
    "player_hands",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("game_id", String, ForeignKey("games.id"), nullable=False),
    Column("player_id", String, ForeignKey("players.id"), nullable=False),
    Column("type", String, nullable=False),
    Column("name", String, nullable=False),
)
