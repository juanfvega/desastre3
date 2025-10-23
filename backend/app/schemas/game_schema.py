from pydantic import BaseModel
from typing import Optional

class GameIn(BaseModel):
    nameGame: str
    num_players: int
    player_id: str
    password: Optional[str] = None

class GameOut(BaseModel):
    id: str
    host_id: str
    nameGame: str
    num_players: int
    password: Optional[str] = None
    status: str    

class GameListOut(BaseModel):
    id: str
    nameGame: str
    num_players: int
    status: str
from typing import Optional, List


class StartGameRequest(BaseModel):
    player_id: str


class StartGameResponse(BaseModel):
    success: bool
    game_id: str
    status: str

class JoinGameRequest(BaseModel):
    player_id: str

class JoinGameResponse(BaseModel):
    success: bool
    game_id: str
    players_count: int

class PreparationRoundResponse(BaseModel):
    success: bool
    game_id: str
    preparation_round_finished: bool
    next_phase: Optional[str] = None
    issues: Optional[List[str]] = None
    message: Optional[str] = None

class TurnInfoResponse(BaseModel):
    game_id: str
    current_turn: Optional[str]  # player_id

class TurnChangedEvent(BaseModel):
    type: str = "turn_changed"
    game_id: str
    current_turn: str  # player_id

class SelectedCard(BaseModel):
    card_id: int
    
class RobSetResponse(BaseModel):
    success: bool
    message: str
    set_robbed: Optional[str] = None
    attacker_id: str
    target_id: str
    cards_discarded: Optional[List[str]] = None
    
class RobSetRequest(BaseModel):
    attacker_player_id: str
    target_player_id: str
