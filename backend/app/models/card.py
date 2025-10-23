from typing import Optional
from pydantic import BaseModel

class Card(BaseModel):
    id: str
    figure: str  # nombre de la figura, ej. "Poirot", "Marple"

class DiscardCardIn(BaseModel):
    card_id: str #es el nombre de la carta, es que en el front usan el nombre de id

#Se pueden añadir mas datos para pedir al front segun lo que necesite el efecto
class PlayCardRequest(BaseModel):
    target_player_id: Optional[str] = None  # jugador objetivo, si aplica
    player_hand: Optional[bool] = None # si se jugo con solo cartas en la mano (por los sets)
    attacker_player_id: Optional[str] = None