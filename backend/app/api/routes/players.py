from fastapi import APIRouter, HTTPException
from app.schemas.player_schema import PlayerIn, PlayerOut
from app.services.player_service import create_or_update_player
from app.core.database import database

router = APIRouter()


@router.post("/players", response_model=PlayerOut, status_code=201)
async def register_player(player_in: PlayerIn):
    try:
        print(f"Creating player with: username={player_in.username}, birthdate={player_in.birthdate}, avatar={player_in.avatar}")
        player = await create_or_update_player(
            username=player_in.username,
            birthdate=player_in.birthdate,
            avatar=player_in.avatar
        )
        print(f"Player created/updated: {player}")
        return player
    except Exception as e:
        print(f"Error creating player: {e}")
        raise HTTPException(status_code=400, detail=str(e))