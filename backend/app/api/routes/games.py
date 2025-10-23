import json
import random
from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Body
from app.models import detective_sets
from app.schemas.game_schema import GameIn, GameOut, GameListOut, RobSetRequest, RobSetResponse,SelectedCard, StartGameRequest, StartGameResponse, JoinGameRequest, JoinGameResponse
from app.services import game_service, card_services
from app.services.privacy_services import validate_player_access
from app.managers.connection_manager import manager
from app.core.database import database
from app.models.game import GameStatus, games, TurnPhase, Action
from app.models.deck import deck_cards
from app.models.hand import player_hands
from app.models.secret import player_secrets
from app.models.player import players_table
from app.services.auto_discard_service import auto_discard_if_needed
from sqlalchemy import select, func, update, insert
from app.managers.connection_manager import manager as websocket_manager
from app.models.card import DiscardCardIn, PlayCardRequest, PlayCardRequest
from pydantic import BaseModel
from app.services.skip_action_services import skip_discard_and_draw
from app.services.cards_effects_services import can_play_card, play_card

router = APIRouter()

# === GAMES: crear y listar ===
@router.post("/games", response_model=GameOut, status_code=status.HTTP_201_CREATED)
async def create_public_game(payload: GameIn):
    try:
        return await game_service.create_game(payload.nameGame, payload.num_players, payload.player_id, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/games", response_model=list[GameListOut])
async def get_games():
    try:
        return await game_service.list_public_games()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === GAMES: start / join ===
@router.post("/games/{game_id}/start", response_model=StartGameResponse)
async def start_game(game_id: str, request: StartGameRequest):
    try:
        game = await game_service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.host != request.player_id:
            raise HTTPException(status_code=403, detail="Only the host can start the game")
        if game.status != GameStatus.WAITING:
            raise HTTPException(status_code=409, detail=f"Game is in state: {game.status.value.lower()}")
        if len(game.players) < game.num_players:
            raise HTTPException(status_code=400, detail="Insufficient players")

        await game_service.start_game(game_id)
        
        # 🔁 Releer para tomar el turno actualizado luego del start
        game = await game_service.get_game(game_id)
        current_player_id = game.current_turn_player

        # Obtener nombre del jugador actual
        current_player_name = await database.fetch_val(
            select(players_table.c.username).where(players_table.c.id == current_player_id)
        ) or current_player_id

        # Notificar turno inicial al FE (compat con TurnPanel)
        await websocket_manager.broadcast_to_game(
            {
                "event": "turn.update",
                "gameId": game_id,
                "activePlayerId": current_player_id,
                "activePlayerName": current_player_name,
                "phase": TurnPhase.ACTION.value,
                "lastAction": Action.NONE.value,
                "canEndTurn": False,
            },
            game_id
        )
        
        return StartGameResponse(success=True, game_id=game_id, status="started")

    except ValueError as e:
        msg = str(e)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="Game not found")
        elif "in" in msg and "state" in msg:
            raise HTTPException(status_code=409, detail=msg)
        elif "Insufficient" in msg:
            raise HTTPException(status_code=400, detail="Insufficient players")
        else:
            raise HTTPException(status_code=400, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/games/{game_id}/join", response_model=JoinGameResponse)
async def join_game(game_id: str, request: JoinGameRequest):
    player_id = request.player_id
    try:
        game = await game_service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        player = await game_service.get_player(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        if game.status != GameStatus.WAITING:
            raise HTTPException(status_code=409, detail=f"Game is in state: {game.status.value.lower()}")

        if len(game.players) >= game.num_players:
            raise HTTPException(status_code=409, detail="Game has no places left")

        game = await game_service.join_game(game_id, player_id)
        return JoinGameResponse(success=True, game_id=game_id, players_count=len(game.players))

    except HTTPException:
        raise
    
    except Exception as e:
        msg = str(e)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="Game not found")
        elif "in" in msg and "state" in msg:
            raise HTTPException(status_code=409, detail=msg)
        elif "no places left" in msg:
            raise HTTPException(status_code=409, detail="Game has no places left")
        else:
            raise HTTPException(status_code=400, detail=msg)

# === DEAL: repartir cartas + broadcast ===
@router.post("/games/{game_id}/deal", status_code=status.HTTP_200_OK)
async def deal_cards(game_id: str):
    """
    Task 3.2: Reparte todas las cartas aleatoriamente, una por una, a cada jugador.
    Respuesta: resumen por jugador (privacidad).
    """
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if len(game.players) < 1:
        raise HTTPException(status_code=400, detail="No players to deal")

    # Verificar que el juego esté en preparación
    if game.status != GameStatus.PREPARATION:
        raise HTTPException(status_code=400, detail="Game must be in preparation state to deal cards")

    # Inicializar el mazo si no existe
    await card_services.initialize_deck(game_id)
    
    # Repartir cartas
    await card_services.deal_cards_round_robin(game_id)

    # Resumen (sin exponer cartas)
    summary = []
    for pid in game.players:
        # Contar cartas en la mano del jugador desde la base de datos
        count_query = "SELECT COUNT(*) as count FROM player_hands WHERE player_id = :player_id"
        result = await database.fetch_one(count_query, {"player_id": pid})
        count = result["count"] if result else 0
        summary.append({"player_id": pid, "hand_count": count})
    
    #notificar por WS
    try:
        await websocket_manager.broadcast_to_game({"event": "cards_dealt", "game_id": game_id}, game_id)
    except Exception as e:
        print(f"[WS] Broadcast error on /deal: {e}")

    return {"success": True, "game_id": game_id, "summary": summary}

# === CARTAS: mano del jugador (acepta game_id opcional) ===
@router.get("/player/cards/{player_id}")
async def get_player_cards(player_id: str, game_id: Optional[str] = Query(None)):
    # Si viene game_id en query lo usamos; sino inferimos
    if not game_id:
        game_id_row = await database.fetch_one(
            "SELECT DISTINCT game_id FROM player_hands WHERE player_id = :player_id LIMIT 1",
            {"player_id": player_id},
        )
        if not game_id_row:
            row = await database.fetch_one(
                "SELECT at_game FROM players WHERE id = :player_id", {"player_id": player_id}
            )
            if not row or not row["at_game"]:
                raise HTTPException(status_code=404, detail="Player not found in any game")
            game_id = row["at_game"]
        else:
            game_id = game_id_row["game_id"]

    await validate_player_access(game_id, player_id, player_id)

    rows = await database.fetch_all(
        player_hands.select().where(
            (player_hands.c.player_id == player_id) & (player_hands.c.game_id == game_id)
        )
    )
    return [{"type": r["type"], "name": r["name"]} for r in rows]


# ===cantidad del MAZO + mazo de DESCARTE ===
@router.get("/games/{game_id}/mazos")
async def get_mazos(game_id: str):
    count_query = (
        select(func.count())
        .select_from(deck_cards)
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == 1)
    )

    count = await database.fetch_val(count_query)
    count = count or 0

    discard_query = (
        select(deck_cards.c.type, deck_cards.c.name, deck_cards.c.id)
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == 0)
        .order_by(deck_cards.c.id.asc())
    )
    discard_rows = await database.fetch_all(discard_query)

    seen = set()
    descarte = []
    for r in discard_rows:
        key = (r["type"], r["name"])
        if key not in seen:
            seen.add(key)
            descarte.append({"type": r["type"], "name": r["name"]})

    return {"countMazo": int(count), "descarteVisible": descarte}

@router.post("/games/{game_id}/draft/{player_id}/{card_name}")
async def draft_card_route(game_id: str, player_id: str, card_name: str):
    """Permite a un jugador tomar una carta del draft."""
    try:
        result = await card_services.draft_card_to_hand(game_id, player_id, card_name)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al tomar del draft: {e}")

@router.post("/games/{game_id}/turn/end")
async def end_turn(game_id: str, player_id: str):
    """
    STORY 15: Descarte obligatorio al finalizar turno.
    Si el jugador activo no descarta manualmente y tiene más de 6 cartas,
    se fuerza un descarte aleatorio y se roba hasta mantener 6 cartas.
    """
    from app.services.auto_discard_service import auto_discard_if_needed

    # Verificar que la partida existe
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Verificar que el jugador pertenece a la partida
    if player_id not in game.players:
        raise HTTPException(status_code=403, detail="Player not in this game")

    # Verificar que sea su turno
    if game.current_turn_player != player_id:
        raise HTTPException(status_code=403, detail="It's not your turn")

    # Ejecutar descarte automático si aplica
    result = await auto_discard_if_needed(game_id, player_id)

    # Avanzar turno al siguiente jugador
    if hasattr(game_service, "advance_turn"):
        await game_service.advance_turn(game_id)
    elif hasattr(game_service, "next_turn"):
        await game_service.next_turn(game_id)
    # (esto permite compatibilidad con ambas versiones del backend)

    # Devolver respuesta
    return {
        "success": True,
        "message": "Turn ended successfully (auto-discard applied if needed)",
        "discard_summary": result,
    }

# === draw ===
@router.post("/games/{game_id}/players/{player_id}/draw", status_code=status.HTTP_200_OK)
async def draw_cards(game_id: str, player_id: str):
    """
    Como jugador activo, quiero robar cartas para completar mi mano.
    Si el mazo regular se vacía al intentar robar, la partida finaliza.
    """
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != GameStatus.PLAYING:
        raise HTTPException(status_code=400, detail="Game must be in playing state to draw cards")

    if game.current_turn_player != player_id:
        raise HTTPException(status_code=403, detail="Not your turn")

    # Contar cartas actuales en mano
    hand_count = await database.fetch_val(
        select(func.count())
        .select_from(player_hands)
        .where(player_hands.c.game_id == game_id)
        .where(player_hands.c.player_id == player_id)
    ) or 0

    cards_to_draw = 6 - hand_count
    if cards_to_draw <= 0:
        return {"message": "No cards to draw"}

    # Verificar cuántas cartas quedan en el mazo
    remaining_cards = await database.fetch_all(
        select(deck_cards)
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == 1)
        .order_by(deck_cards.c.id.asc())
    )

    remaining_count = len(remaining_cards)

    if cards_to_draw >= remaining_count:
        # Asignar todas las cartas restantes al jugador
        random.shuffle(remaining_cards) #cartas en orden azar
        remaining_ids = [c["id"] for c in remaining_cards]
        
        for card in remaining_cards:
            await database.execute(
                insert(player_hands).values(
                    id=card["id"],
                    player_id=player_id,
                    game_id=game_id,
                    type=card["type"],
                    name=card["name"]
                )
            )

        # Eliminar las cartas del mazo
        await database.execute(
            deck_cards.delete()
            .where(deck_cards.c.game_id == game_id)
            .where(deck_cards.c.id.in_(remaining_ids))
        )

        # Finalizar partida
        await database.execute(
            update(games)
            .where(games.c.id == game_id)
            .values(status=GameStatus.FINISHED)
        )
        
        await manager.broadcast_to_game({
            "event": "game_end",
            "game_id": game_id,
            "winner": player_id,
            "message": "The game has ended! Murderer escapes!",
        }, game_id)

        return {
            "message": "Game finished! Murderer escapes!",
            "winner": player_id,
        }

    drawn_cards = await card_services.draw_cards(game_id, player_id, cards_to_draw)
    if not drawn_cards:
        return {"message": "No cards left in the deck"}

    return {
        "message": "Cards drawn successfully",
        "cards": drawn_cards,
        "remaining_in_deck": remaining_count - cards_to_draw
    }


# === TURNOS: obtener turno actual (para FE) ===
@router.get("/games/turn/{game_id}")
async def get_current_turn(game_id: str):
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Leer directamente de la base de datos para obtener turn_phase y last_action
    game_row = await database.fetch_one(
        select(games).where(games.c.id == game_id)
    )
    
    return {
        "gameId": game_id,
        "currentTurnPlayerId": game.current_turn_player,
        "phase": game_row["turn_phase"] if game_row and game_row["turn_phase"] else TurnPhase.ACTION.value,
        "lastAction": game_row["last_action"] if game_row and game_row["last_action"] else Action.NONE.value
    }

# === SECRETOS: asignar (roles) + obtener ===
@router.post("/games/{game_id}/deal_secrets", status_code=status.HTTP_200_OK)
async def deal_secrets(game_id: str):
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not game.players:
        raise HTTPException(status_code=400, detail="No players to assign secrets")

    players = list(game.players)
    random.shuffle(players)
    roles = {}

    # Reglas: 2 jugadores => sin cómplice
    if len(players) >= 3:
        roles[players[0]] = "asesino"
        roles[players[1]] = "cómplice"
        for pid in players[2:]:
            roles[pid] = "inocente"
    
    elif len(players) == 2:
        roles[players[0]] = "asesino"
        roles[players[1]] = "inocente"
    else:
        roles[players[0]] = "inocente"

    # Persistir roles (limpiar y reinsertar)
    await database.execute(
        player_secrets.delete().where(player_secrets.c.game_id == game_id)
    )
    await database.execute_many(
        player_secrets.insert(),
        [{"game_id": game_id, "player_id": pid, "secret": role, "revealed": 0}
         for pid, role in roles.items()],
    )

    # Notificar al frontend
    try:
        await websocket_manager.broadcast_to_game(
            {"event": "secrets_dealt", "game_id": game_id}, game_id
        )
    except Exception as e:
        print(f"[WS] error broadcasting secrets_dealt: {e}")

    return {"success": True, "assigned": roles}

@router.get("/player/secrets/{player_id}")
async def get_player_secrets(player_id: str, game_id: Optional[str] = Query(None)):
    # si no viene game_id, inferir desde players.at_game
    if not game_id:
        row = await database.fetch_one(
            select(players_table.c.at_game).where(players_table.c.id == player_id)
        )
        game_id = row["at_game"] if row and row["at_game"] else None
    if not game_id:
        raise HTTPException(status_code=404, detail="Player not found in any game")

    await validate_player_access(game_id, player_id, player_id)

    rows = await database.fetch_all(
        player_secrets.select().where(
            (player_secrets.c.game_id == game_id) & (player_secrets.c.player_id == player_id)
        )
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Secret not found")

    r = rows[0]
    return [{"secret": r["secret"], "revealed": bool(r["revealed"])}]

@router.get("/games/player/secrets/{player_id}")
async def get_player_secrets_alias(player_id: str):
    return await get_player_secrets(player_id)

#13
@router.post("/games/{game_id}/{player_id}/descarte", status_code=status.HTTP_200_OK)
async def discard_card_route(game_id: str, player_id: str, payload: DiscardCardIn):
    """
    Descarta una carta usando el nombre de la mano
    """
    try:
        result = await card_services.discard_card(game_id, player_id, payload.card_id)
        
        # Actualizar turn_phase y last_action
        await database.execute(
            update(games)
            .where(games.c.id == game_id)
            .values(
                turn_phase=TurnPhase.READY_TO_END,
                last_action=Action.DISCARD
            )
        )
        
        # Contar cartas en mazo (draw pile)
        draw_pile_count = await database.fetch_val(
            select(func.count())
            .select_from(deck_cards)
            .where(
                (deck_cards.c.game_id == game_id)
                & (deck_cards.c.in_deck == True)
                & (deck_cards.c.in_card_draft == False)
            )
        ) or 0
        # Notificación de mazo (para refrescar UI)
        try:
            await websocket_manager.broadcast_to_game(
                {
                    "event": "deck_updated",
                    "payload": {
                        "discard": result.get("top_discard"),
                        "regularCount": draw_pile_count,
                    }
                },
                game_id
            )
        except Exception as e:
            print(f"[WS] error broadcasting deck_updated: {e}")
        
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# === SKIP ACTION: descartar/robar y marcar turno listo para terminar ===
class SkipActionIn(BaseModel):
    player_id: str

@router.post("/games/{game_id}/skip_action", status_code=status.HTTP_200_OK)
async def skip_action(game_id: str, payload: SkipActionIn = Body(...)):
    """
    Botón 'No ejecutar acción':
      - Descarta 1 carta aleatoria de la mano (si hay).
      - Roba 1 del mazo.
      - Marca la acción como SKIP_ACTION y turn_phase como READY_TO_END.
      - Notifica al FE con 'turn.update' (compat TurnPanel).
    """
    player_id = payload.player_id

    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if player_id not in game.players:
        raise HTTPException(status_code=403, detail="Player not in this game")
    if game.current_turn_player != player_id:
        raise HTTPException(status_code=403, detail="It's not your turn")

    # Ejecuta descarte+robo específicos del skip
    result = await skip_discard_and_draw(game_id, player_id)

    # Persistir fase/acción del turno
    await database.execute(
        games.update()
        .where(games.c.id == game_id)
        .values(
            turn_phase=TurnPhase.READY_TO_END,
            last_action=Action.SKIP_ACTION,
        )
    )

    # Obtener nombre del jugador
    player_name = await database.fetch_val(
        select(players_table.c.username).where(players_table.c.id == player_id)
    ) or player_id

    # Notificación de mazo (para refrescar UI)
    try:
        await websocket_manager.broadcast_to_game(
            {
                "event": "deck_updated",
                "payload": {
                    "regularCount": result.get("draw_pile_count", 0),
                    "discard": result.get("top_discard"),
                }
            },
            game_id
        )
    except Exception as e:
        print(f"[WS] error broadcasting deck_updated: {e}")

    # Notificación de estado de turno (compat TurnPanel)
    payload_out = {
        "event": "turn.update",
        "gameId": game_id,
        "activePlayerId": player_id,
        "activePlayerName": player_name,
        "phase": TurnPhase.READY_TO_END.value,
        "lastAction": Action.SKIP_ACTION.value,
        "canEndTurn": True,
        "discarded": result.get("discarded"),
        "drawn": result.get("drawn"),
        "message": f"{player_name} no ejecutó acción, descartó 1 y robó 1. Puede terminar su turno."
    }
    await websocket_manager.broadcast_to_game(payload_out, game_id)

    return {"success": True, "result": payload_out}

@router.post("/games/{game_id}/turns/end", status_code=status.HTTP_200_OK)
async def end_turn(game_id: str, request: dict):
    """
    Endpoint Story 16: Terminar turno.
    Solo el jugador activo puede llamarlo.
    """
    player_id = request.get("player_id")
    if not player_id:
        raise HTTPException(status_code=400, detail="player_id is required")

    try:
        result = await game_service.end_turn(game_id, player_id)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#  STORY P0.4: Ver Sets 
@router.get("/games/{game_id}/watch_set", status_code=status.HTTP_200_OK)
async def watch_sets(game_id: str):
    """
    STORY P0.4: Ver sets de detectives jugados por todos los jugadores.
    Muestra los sets visibles agrupados por jugador.
    """
    from app.models.secret import player_secrets
    from app.models.player import players_table
    from app.models.game import games
    from app.core.database import database
    from app.services import game_service

    # Verificar que el juego existe
    game = await database.fetch_one(games.select().where(games.c.id == game_id))
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Consultar los secretos activos del juego (roles / sets visibles)
    query = player_secrets.select().where(player_secrets.c.game_id == game_id)
    rows = await database.fetch_all(query)

    if not rows:
        return {"game_id": game_id, "sets": []}

    # Construir estructura agrupada por jugador
    sets_by_player = {}
    for row in rows:
        pid = row["player_id"]

        # Obtener nombre del jugador
        username = await database.fetch_val(
            players_table.select()
            .with_only_columns(players_table.c.username)
            .where(players_table.c.id == pid)
        )

        # Inicializar estructura si no existe
        if pid not in sets_by_player:
            sets_by_player[pid] = {
                "player_id": pid,
                "player_name": username or f"Jugador {pid[:5]}",
                "sets": []
            }

        # Añadir info de set (aquí podrías reemplazar por tus datos reales de detectives)
        sets_by_player[pid]["sets"].append({
            "detective": row["secret"],           # tipo de detective (ej. "Poirot", "Marple")
            "cards_count": 3,                     # valor simbólico; ajustar si tenés datos reales
            "has_harley_quinn": False,            # placeholder
            "revealed": bool(row["revealed"])
        })

    result = {
        "game_id": game_id,
        "sets": list(sets_by_player.values())
    }

    # Emitir actualización por WebSocket (para actualizar UI)
    await game_service.broadcast_sets_update(game_id, result["sets"])

    return result

@router.get("/games/{game_id}/{player_id}/{card_name}/can_play_card", status_code=status.HTTP_200_OK)
async def get_can_play_card(game_id: str, player_id: str, card_name: str):
    """
    Verifica si un jugador puede jugar la carta indicada.
    Devuelve:
    {
        "can_play": bool, # se puede jugar
        "by_hand": bool, # se puede jugar por las cartas en mano
        "by_table": bool # se puede jugar porque hay un set en mesa
    }
    """
    try:
        result = await can_play_card(game_id, player_id, card_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/games/{game_id}/{player_id}/{card_name}/play_card", status_code=status.HTTP_200_OK)
async def post_play_card(game_id: str, player_id: str, card_name: str, body: PlayCardRequest):
    """
    Juega la carta indicada.
    
    Body opcional, para efectos que lo requieran ejemplo:
    {
        "target_player_id": "p2",   # si la carta necesita un jugador objetivo por ejemplo
    }
    se le pueden añadir mas campos si se necesitan mas datos del front el modelo esta en app/models/card
    
    Devuelve (depende de la carta jugada):
    
    Detectives entra:
    body
    {
        player_hand: bool   indica si se jugo por set en mano o por set en mesa True = mano / False = mesa
    }
    
    y sale por ejemplo:
    {
        "effect": "secret_reveal",
        "card_name": "detective_brent",
        "set_create": true,
        "player_id": "p1",
        "success": true
    }
    
    Los demás tipos (event, instant, devious) aún a implementar.
    """
    try:
        result = await play_card(game_id, player_id, card_name,extra_data=body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Obtener sets
@router.get("/games/{game_id}/sets", status_code=status.HTTP_200_OK)
async def get_sets(game_id: str):
    """
    Ejemplo de retorno:
    {
      "Jugador1": [
          [{"cards": [{"name":"detective_poirot"},{"name":"detective_quin"}]}],
          [{"cards": [{"name":"detective_marple"},{"name":"detective_marple"}]}]
      ],
      "Jugador2": [
          [{"cards": [{"name":"detective_brent"},{"name":"detective_brent"},{"name":"detective_quin"}]}]
      ]
    }
    """
    try:
        return await card_services.get_detective_sets_by_game(game_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/games/{game_id}/watch_discard_pile/{player_id}")
async def watch_discard_pile(game_id: str, player_id: str):
    print(f"game_id recibido: '{game_id}', player_id recibido: '{player_id}'")
    if not game_id or not player_id:
        raise HTTPException(status_code=400, detail="game_id and player_id are required")   
    # Validar que el jugador tenga acceso al juego
    await validate_player_access(game_id, player_id, player_id)

    # Obtener el mazo de descarte las últimas 5 cartas
    discard_query = (
        select(deck_cards.c.type, deck_cards.c.name, deck_cards.c.id)
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == 0)
        # 5 cartas en orden descendente del mazo de descarte
        .order_by(deck_cards.c.id.desc())
        .limit(5)
    )
    
    discard_rows = await database.fetch_all(discard_query)
    print(f"Discard rows en watch_discard_pile: {discard_rows}")
    if len(discard_rows) == 0:
        raise HTTPException(status_code=404, detail="No cards in discard pile")

    # retornar en orden descendente del mazo de descarte
    return [
        {"id": r["id"], "type": r["type"], "name": r["name"]}
        for r in discard_rows
    ]

@router.post("/games/{game_id}/selected_card_in_hand/{player_id}")
async def select_card_in_hand(game_id: str, player_id: str, data: SelectedCard):
    card = data.card_id
    card_id = int(card) if card is not None else None
    print(f"game_id recibido: '{game_id}', player_id recibido: '{player_id}', card_id recibido: '{card_id}'")
    if not game_id or not player_id or not card_id:
        raise HTTPException(status_code=400, detail="game_id, player_id and card_id are required")
    # Validar que el jugador tenga acceso al juego
    await validate_player_access(game_id, player_id, player_id)

    # selecciono la carta del mazo de descarte y luego obtengo su type y name
    # in_deck=False && in_card_draft=False => carta está en el descarte (discard pile, visible)
    card_query = (
        select(deck_cards.c.type, deck_cards.c.name)
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.id == card_id)
        .where(deck_cards.c.in_deck == 0)
        .where(deck_cards.c.in_card_draft == 0)
    )   

    card_data = await database.fetch_one(card_query)
    if not card_data:
        raise HTTPException(status_code=404, detail="Card not found")   
    card_type = card_data["type"]
    card_name = card_data["name"]
    print(f"Card data obtenida: type='{card_type}', name='{card_name}'")
    # Añadir la carta a la mano del jugador
    insert_query = player_hands.insert().values(
        game_id=game_id,
        player_id=player_id,
        type=card_type,
        name=card_name
    )
    await database.execute(insert_query)
    # Marcar la carta como retirada del mazo de descarte
    update_query = (
        deck_cards.update()
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.id == card_id)
        .values(in_deck=None, in_card_draft=None)  # No está en el mazo ni en el draft
    )
    await database.execute(update_query)
    
    # obtener nuevo estado del mazo de descarte
    discard_query = (
        select(deck_cards.c.type, deck_cards.c.name)
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == 0)
        .order_by(deck_cards.c.id.desc())
    )
    discard_rows = await database.fetch_all(discard_query)
    discard_cards_list = [{"type": r["type"], "name": r["name"]} for r in discard_rows]

    # datos para el broadcast a los jugadores
    broadcast_data = {
        "event": "discard_updated",
        "game_id": game_id,
        "discard_cards": discard_cards_list
    }
    # Enviar actualización a todos los jugadores en el juego
    await manager.broadcast_to_game(broadcast_data, game_id)

    return {"detail": "Carta añadida en la mano del jugador"}

# === ROBAR SET ===
@router.post("/games/{game_id}/rob_set", response_model=RobSetResponse, status_code=status.HTTP_200_OK)
async def rob_set(game_id: str, request: PlayCardRequest):
    """
    Endpoint para ejecutar la acción "Robar Set" con la carta "Another Victim".
    
    El jugador atacante puede robar un set completo de otro jugador si:
    - Tiene la carta "Another Victim" en su mano
    - Es su turno
    - El objetivo tiene al menos un set
    - El objetivo no cancela con "Not So Fast"
    """
    try:
        
        attacker_id = request.attacker_player_id
        
        result = await can_play_card(game_id, attacker_id, "event_anothervictim")
        if not result.get("can_play", False):
            raise HTTPException(status_code=404, detail="no se puede jugar la carta")
        
        result = await play_card(game_id, attacker_id, "event_anothervictim",extra_data=request)
        
        discarted = await card_services.discard_card(game_id, attacker_id, "event_anothervictim")
        
        # Actualizar turn_phase y last_action
        await database.execute(
            update(games)
            .where(games.c.id == game_id)
            .values(
                turn_phase=TurnPhase.READY_TO_END,
                last_action=Action.PLAYED
            )
        )
        
        # Contar cartas en mazo (draw pile)
        draw_pile_count = await database.fetch_val(
            select(func.count())
            .select_from(deck_cards)
            .where(
                (deck_cards.c.game_id == game_id)
                & (deck_cards.c.in_deck == True)
                & (deck_cards.c.in_card_draft == False)
            )
        ) or 0
        # Notificación de mazo (para refrescar UI)
        try:
            await websocket_manager.broadcast_to_game(
                {
                    "event": "deck_updated",
                    "payload": {
                        "discard": discarted.get("top_discard"),
                        "regularCount": draw_pile_count,
                    }
                },
                game_id
            )
        except Exception as e:
            print(f"[WS] error broadcasting deck_updated: {e}")
            
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    #
    # # === VALIDACIONES INICIALES ===
    # game = await game_service.get_game(game_id)
    # if not game:
    #     raise HTTPException(status_code=404, detail="Game not found")
    #
    # if game.status != GameStatus.PLAYING:
    #     raise HTTPException(status_code=400, detail="Game must be in playing state")
    #
    # if attacker_id not in (game.players or []):
    #     raise HTTPException(status_code=403, detail="Attacker is not in this game")
    #
    # if target_id not in (game.players or []):
    #     raise HTTPException(status_code=403, detail="Target is not in this game")
    #
    # if attacker_id == target_id:
    #     raise HTTPException(status_code=400, detail="Cannot rob from yourself")
    #
    # if game.current_turn_player != attacker_id:
    #     raise HTTPException(status_code=403, detail="Not your turn")
    #
    # # Verificar que el atacante tiene "Another Victim"
    # attacker_hand = await database.fetch_all(
    #     select(player_hands).where(
    #         (player_hands.c.game_id == game_id) &
    #         (player_hands.c.player_id == attacker_id) &
    #         (player_hands.c.name == "Another Victim")
    #     )
    # )
    # 
    # if not attacker_hand:
    #     raise HTTPException(status_code=400, detail="Attacker does not have 'Another Victim' card")
    #
    # # Obtener sets del objetivo (solo columnas necesarias para compatibilidad)
    # target_sets_rows = await database.fetch_all(
    #     select(player_secrets.c.id, player_secrets.c.secret).where(
    #         (player_secrets.c.game_id == game_id) &
    #         (player_secrets.c.player_id == target_id)
    #     )
    # )
    #
    # target_sets = [{"id": r["id"], "secret": r["secret"]} for r in target_sets_rows]
    #
    # # === LÓGICA DEL ROBO ===
    # async with database.transaction():
    #     # FLUJO B: Objetivo no tiene sets
    #     if not target_sets:
    #         # Descartar "Another Victim"
    #         await database.execute(
    #             player_hands.delete().where(
    #                 (player_hands.c.game_id == game_id) &
    #                 (player_hands.c.player_id == attacker_id) &
    #                 (player_hands.c.name == "Another Victim")
    #             )
    #         )
    #
    #         target_player = await game_service.get_player(target_id)
    #         target_name = target_player.username if target_player else target_id
    #
    #         result = RobSetResponse(
    #             success=False,
    #             message=f"{target_name} no tiene sets para robar",
    #             attacker_id=attacker_id,
    #             target_id=target_id,
    #             cards_discarded=["Another Victim"]
    #         )
    #
    #         # Broadcast a todos los jugadores
    #         await websocket_manager.broadcast_to_game({
    #             "event": "rob_set_result",
    #             "game_id": game_id,
    #             "success": False,
    #             "message": result.message,
    #             "attacker_id": attacker_id,
    #             "target_id": target_id,
    #             "cards_discarded": ["Another Victim"]
    #         }, game_id)
    #
    #         return result
    #
    #     # FLUJO A y C: Objetivo tiene sets
    #     # Verificar si el objetivo tiene "Not So Fast"
    #     target_hand = await database.fetch_all(
    #         select(player_hands).where(
    #             (player_hands.c.game_id == game_id) &
    #             (player_hands.c.player_id == target_id) &
    #             (player_hands.c.name == "Not So Fast")
    #         )
    #     )
    #
    #     has_not_so_fast = len(target_hand) > 0
    #
    #     if has_not_so_fast:
    #         # FLUJO C: Cancelar robo
    #         # Descartar "Another Victim"
    #         await database.execute(
    #             player_hands.delete().where(
    #                 (player_hands.c.game_id == game_id) &
    #                 (player_hands.c.player_id == attacker_id) &
    #                 (player_hands.c.name == "Another Victim")
    #             )
    #         )
    #
    #         # Descartar "Not So Fast"
    #         await database.execute(
    #             player_hands.delete().where(
    #                 (player_hands.c.game_id == game_id) &
    #                 (player_hands.c.player_id == target_id) &
    #                 (player_hands.c.name == "Not So Fast")
    #             )
    #         )
    #
    #         target_player = await game_service.get_player(target_id)
    #         target_name = target_player.username if target_player else target_id
    #
    #         result = RobSetResponse(
    #             success=False,
    #             message=f"{target_name} canceló el robo con Not So Fast",
    #             attacker_id=attacker_id,
    #             target_id=target_id,
    #             cards_discarded=["Another Victim", "Not So Fast"]
    #         )
    #
    #         # Broadcast a todos los jugadores
    #         await websocket_manager.broadcast_to_game({
    #             "event": "rob_set_result",
    #             "game_id": game_id,
    #             "success": False,
    #             "message": result.message,
    #             "attacker_id": attacker_id,
    #             "target_id": target_id,
    #             "cards_discarded": ["Another Victim", "Not So Fast"]
    #         }, game_id)
    #
    #         return result
    #
    #     else:
    #         # FLUJO A: Robo exitoso
    #         # Seleccionar un set random del objetivo
    #         robbed_set = random.choice(target_sets)
    #
    #         # Transferir el set al atacante
    #         await database.execute(
    #             player_secrets.update()
    #             .where(player_secrets.c.id == robbed_set["id"])
    #             .values(player_id=attacker_id)
    #         )
    #
    #         # Descartar "Another Victim"
    #         await database.execute(
    #             player_hands.delete().where(
    #                 (player_hands.c.game_id == game_id) &
    #                 (player_hands.c.player_id == attacker_id) &
    #                 (player_hands.c.name == "Another Victim")
    #             )
    #         )
    #
    #         attacker_player = await game_service.get_player(attacker_id)
    #         target_player = await game_service.get_player(target_id)
    #
    #         attacker_name = attacker_player.username if attacker_player else attacker_id
    #         target_name = target_player.username if target_player else target_id
    #
    #         result = RobSetResponse(
    #             success=True,
    #             message=f"{attacker_name} robó el set '{robbed_set['secret']}' de {target_name}",
    #             set_robbed=robbed_set["secret"],
    #             attacker_id=attacker_id,
    #             target_id=target_id,
    #             cards_discarded=["Another Victim"]
    #         )
    #
    #         # Broadcast a todos los jugadores
    #         await websocket_manager.broadcast_to_game({
    #             "event": "rob_set_result",
    #             "game_id": game_id,
    #             "success": True,
    #             "message": result.message,
    #             "set_robbed": robbed_set["secret"],
    #             "attacker_id": attacker_id,
    #             "target_id": target_id,
    #             "cards_discarded": ["Another Victim"]
    #         }, game_id)
    #
        

    