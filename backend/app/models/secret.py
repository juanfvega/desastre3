from sqlalchemy import Table, Column, Integer, String, ForeignKey, Boolean, UniqueConstraint
from app.core.database import metadata

# Secretos por jugador (1 por jugador al inicio)
# Valores de "secret" típicos: "asesino", "cómplice", "inocente"
# Estados: revelado (False al repartir)
player_secrets = Table(
    "player_secrets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("game_id", String, ForeignKey("games.id"), nullable=False),
    Column("player_id", String, ForeignKey("players.id"), nullable=False),
    Column("secret", String, nullable=False),
    # --- NUEVO secretos ---
    Column("revealed", Boolean, nullable=False, server_default="0"),
    UniqueConstraint("game_id", "player_id", name="uq_secret_per_player_per_game"),
)
