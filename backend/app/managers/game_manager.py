# app/managers/game_manager.py
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, update
from app.core.database import database
from app.models.game import games as games_table, GameStatus
from app.models.player import players_table

MIN_PLAYERS = 2
MAX_PLAYERS = 6

class GameManagerDB:
    """
    Manager orientado a BD (SQLite + databases) para manejar turno actual.
    """

    async def _get_game(self, game_id: str) -> Optional[dict]:
        row = await database.fetch_one(
            select(games_table).where(games_table.c.id == game_id)
        )
        return dict(row) if row else None  

    async def _get_players_in_game(self, game_id: str) -> List[dict]:
        try:
            rows = await database.fetch_all(
                select(players_table)
                .where(players_table.c.at_game == game_id)
                .order_by(
                    players_table.c.created_at.asc(),
                    players_table.c.username.asc()
                )
            )
        except Exception:
            rows = await database.fetch_all(
                select(players_table)
                .where(players_table.c.at_game == game_id)
                .order_by(players_table.c.username.asc())
            )
        return [dict(r) for r in rows]

    async def _validate(self, game_row: Optional[dict], players_count: int):
        if not game_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
            )
        if players_count < MIN_PLAYERS or players_count > MAX_PLAYERS:
            raise HTTPException(
                status_code=400,
                detail=f"Players must be between {MIN_PLAYERS} and {MAX_PLAYERS}",
            )
        if game_row.get("status") not in (
            GameStatus.PREPARATION.value,
            GameStatus.PLAYING.value,
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid game status: {game_row.get('status')}",
            )

    async def get_current_turn_player(self, game_id: str) -> Optional[str]:
        game = await self._get_game(game_id)
        players = await self._get_players_in_game(game_id)
        await self._validate(game, len(players))
        return game.get("current_turn_player")  

    async def set_current_turn_player(self, game_id: str, player_id: str) -> bool:
        game = await self._get_game(game_id)
        players = await self._get_players_in_game(game_id)
        await self._validate(game, len(players))

        if not any(p["id"] == player_id for p in players):
            raise HTTPException(status_code=400, detail="Player not in game")

        await database.execute(
            update(games_table)
            .where(games_table.c.id == game_id)
            .values(current_turn_player=player_id)
        )
        return True

    async def advance_turn_next(self, game_id: str) -> str:
        game = await self._get_game(game_id)
        players = await self._get_players_in_game(game_id)
        await self._validate(game, len(players))

        if not players:
            raise HTTPException(status_code=400, detail="No players in game")

        player_ids = [p["id"] for p in players]
        current = game.get("current_turn_player")

        if not current or current not in player_ids:
            next_id = player_ids[0]
        else:
            idx = player_ids.index(current)
            next_id = player_ids[(idx + 1) % len(player_ids)]

        async with database.transaction():
            await database.execute(
                update(games_table)
                .where(games_table.c.id == game_id)
                .values(current_turn_player=next_id)
            )

        return next_id

game_manager = GameManagerDB()