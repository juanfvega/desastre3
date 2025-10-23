from fastapi import HTTPException
from app.services import game_service

async def validate_player_access(game_id: str, target_player_id: str, requesting_player_id: str):
    """
    Valida que un jugador solo pueda acceder a sus propios datos dentro de un juego específico
    """
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Validar existencia del jugador solicitante en el mismo juego
    if requesting_player_id not in game.players:
        raise HTTPException(status_code=404, detail="Requesting player not found in game")

    # Validar existencia del jugador objetivo en el mismo juego
    if target_player_id not in game.players:
        raise HTTPException(status_code=404, detail="Target player not found in game")

    # Validación de privacidad
    if target_player_id != requesting_player_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only access your own data")
