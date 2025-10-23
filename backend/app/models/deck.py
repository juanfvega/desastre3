from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey
from app.core.database import metadata
from pydantic import BaseModel

# Mazo y descarte visibles (no revelamos contenido del mazo)
# in_deck=True  && in_card_draft=False => carta está en el mazo (draw pile, oculta)
# in_deck=False && in_card_draft=False => carta está en el descarte (discard pile, visible)
# in_deck=None  && in_card_draft=True => carta está en card_draft visible

deck_cards = Table(
    "deck_cards",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("game_id", String, ForeignKey("games.id"), nullable=False),
    Column("type", String, nullable=False),
    Column("name", String, nullable=False),
    #Column("in_deck", Boolean, nullable=False, default=True),
    Column("in_deck", Boolean, nullable=True, default=True),
    Column("in_card_draft", Boolean, nullable=True, default=False),
)
