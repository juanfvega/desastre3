from app.core.database import database
from typing import Optional
from app.managers.connection_manager import connection_manager as manager
import json
from sqlalchemy import insert, select, update, delete,func, and_
from app.models.game import GameStatus, Game, games, TurnPhase, Action
from app.models.player import players_table, Player
from app.models.deck import deck_cards
from datetime import date, datetime, timezone
from uuid import uuid4
from app.managers.game_manager import game_manager
from app.schemas.game_schema import TurnChangedEvent
from app.managers.connection_manager import manager as websocket_manager
from app.models.hand import player_hands

BASE_CARDS = [
    {"type": "Detective", "name": "detective_quin", "amount": 4},
    {"type": "Detective", "name": "detective_oliver", "amount": 3},
    {"type": "Detective", "name": "detective_marple", "amount": 3},
    {"type": "Detective", "name": "detective_pyne", "amount": 3},
    {"type": "Detective", "name": "detective_tommyberesford", "amount": 2},
    {"type": "Detective", "name": "detective_brent", "amount": 3},
    {"type": "Detective", "name": "detective_tuppenceberesford", "amount": 2}, 
    {"type": "Detective", "name": "detective_poirot", "amount": 3},
    {"type": "Detective", "name": "detective_satterthwaite", "amount": 2},
    {"type": "Instant", "name": "instant_notsofast", "amount": 10},
    {"type": "Devious", "name": "devious_blackmailed", "amount": 1},
    {"type": "Devious", "name": "devious_fauxpas", "amount": 3},
    {"type": "Event", "name": "event_deadcardfolly", "amount": 3},
    {"type": "Event", "name": "event_pointsuspicious", "amount": 3},
    {"type": "Event", "name": "event_deadcardfolly", "amount": 3},
    {"type": "Event", "name": "event_anothervictim", "amount": 2},
    {"type": "Event", "name": "event_lookashes", "amount": 3},
    {"type": "Event", "name": "event_cardtrade", "amount": 3},
    {"type": "Event", "name": "event_onemore", "amount": 2},
    {"type": "Event", "name": "event_earlytrain", "amount": 2},
    {"type": "Event", "name": "event_cardsonthetable", "amount": 1},
]

async def create_game(nameGame: str, num_players: int, player_id: str, password: Optional[str] = None):
    
    
    if not isinstance(nameGame, str) or not nameGame.strip():
        raise ValueError("El nombre de la partida (nameGame) es obligatorio")
    if not isinstance(num_players, int) or num_players < 2 or num_players > 6:
        raise ValueError("num_players debe estar entre 2 y 6")

    game_id: str = str(uuid4())
    print(f"Inserting game into DB: id={game_id}, nameGame={nameGame}, num_players={num_players}, host={player_id}")
    query = games.insert().values(
        id=game_id,
        host=player_id, 
        nameGame=nameGame.strip(),
        num_players=num_players,
        password=password,
        status=GameStatus.WAITING,
        current_turn_player = None,
        turn_phase=TurnPhase.ACTION,
        last_action=Action.NONE,
    )
    await database.execute(query)
    
    # Add host to players
    players_json = json.dumps([player_id])
    await database.execute(
        update(games).where(games.c.id == game_id).values(players=players_json)
    )
    
    # Notificamos la creación del juego
    print(f"Broadcasting game creation to game_id={game_id}")
    await manager.broadcast_to_game({
    "event": "game.created",
    "game": {
        "id": game_id,
        "host_id":player_id,
        "nameGame": nameGame.strip(),
        "num_players": num_players,
        "status": GameStatus.WAITING.value
    }
}, game_id)
    print("Broadcast completed")
    
    #set de detectives añadido para hacer pruebas
    
    #despues se borra cuando el jugar set funcione
    
    return {
        "id": game_id,
        "host_id":player_id,
        "nameGame": nameGame.strip(),
        "num_players": num_players,
        "password": password,
        "status": GameStatus.WAITING.value
    }

async def list_public_games():
    query = games.select().where(
        and_(
            games.c.status == GameStatus.WAITING,
            games.c.password == None
        )
    )
    
    return await database.fetch_all(query)

async def save_game(game: Game):
    players_json = json.dumps(game.players or [])
    query = select(games.c.id).where(games.c.id == game.id)
    existing = await database.fetch_one(query)

    if existing:
        q = (
            update(games)
            .where(games.c.id == game.id)
            .values(
                nameGame=game.nameGame,
                status=game.status,
                host=game.host,
                num_players=game.num_players,
                players=players_json,
                current_turn_player=game.current_turn_player
            )
        )
    else:
        q = insert(games).values(
            id=game.id,
            nameGame=game.nameGame,
            status=game.status,
            host=game.host,
            num_players=game.num_players,
            players=players_json,
            current_turn_player=game.current_turn_player,
            deck_initialized=False,
            turn_phase=TurnPhase.ACTION,
            last_action=Action.NONE,
        )
    await database.execute(q)

async def get_game(game_id: str):
    query = select(games).where(games.c.id == game_id)
    row = await database.fetch_one(query)
    if not row:
        return None
    
    raw_players = row["players"]
    if isinstance(raw_players, str):
        players_list = json.loads(raw_players) if raw_players else []
    else:
        players_list = raw_players or []
    
    return Game(
        id=row["id"],
        nameGame=row["nameGame"],
        host=row["host"],
        num_players=row["num_players"],
        status=row["status"],
        current_turn_player=row["current_turn_player"],
        players=players_list,
    )

async def join_game(game_id: str, player_id: str):
    async with database.transaction():
        username_q = select(players_table).where(players_table.c.id == player_id)
        player_row = await database.fetch_one(username_q)
        if not player_row:
            return None

        row = await database.fetch_one(select(games).where(games.c.id == game_id))
        if not row:
            return None

        raw_players = row["players"]
        if isinstance(raw_players, str):
            players_list = json.loads(raw_players) if raw_players else []
        else:
            players_list = raw_players or []

        if player_id not in players_list:
            players_list.append(player_id)

        updated_game = Game(
            id=row["id"],
            nameGame=row["nameGame"],
            host=row["host"] or player_id,
            num_players=row["num_players"],
            status=row["status"],
            current_turn_player=row["current_turn_player"],
            players=players_list,
        )

        await save_game(updated_game)

        await _broadcast_player_joined(
            game_id=game_id,
            player_id=player_row["id"],
            player_name=player_row["username"],
            num_players=len(players_list)
        )
        
        # === Crear un set por jugador que se une ===
        try:
            from sqlalchemy import insert
            from app.models.detective_sets import detective_sets

            new_set = {
                "game_id": game_id,
                "player_id": player_id,
                "detective_name": "detective_quin",
                "set_size": 3,
                "cards_used": ["detective_quin", "detective_quin", "detective_quin"],
            }

            await database.execute(insert(detective_sets).values(new_set))
            print(f"✅ Set creado para jugador {player_id} en partida {game_id}")

        except Exception as e:
            import traceback
            print(f"⚠️ Error al insertar set para jugador {player_id}: {e}")
            print(traceback.format_exc())
        # borrar cuando el jugar set funcione

        await _broadcast_lobby_state(updated_game)
        return updated_game

async def delete_game(game_id: str):
    query = delete(games).where(games.c.id == game_id)
    await database.execute(query)

async def save_player(player: Player):
    query = select(players_table.c.id).where(players_table.c.id == player.id)
    existing = await database.fetch_one(query)

    if existing:
        q = (
            update(players_table)
            .where(players_table.c.id == player.id)
            .values(
                username=player.username, 
                birthdate=player.birthdate,
                avatar=player.avatar,
                at_game=player.at_game
            )
        )
    else:
        q = insert(players_table).values(
            id=player.id,
            username=player.username, 
            birthdate=player.birthdate,
            avatar=player.avatar,
            at_game=player.at_game
        )
    await database.execute(q)

async def get_player(player_id: str):
    query = select(players_table).where(players_table.c.id == player_id)
    row = await database.fetch_one(query)
    if not row:
        return None
    return Player(
        id=row["id"], 
        username=row["username"],
        birthdate=row["birthdate"], 
        avatar=row["avatar"],
        at_game=row["at_game"]
    )

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def _build_lobby_state(game: Game):
    players = []
    for pid in game.players or []:
        p = await get_player(pid)
        players.append({"id": pid, "name": p.username if p else pid})
    return {
        "event": "lobby_state",
        "gameId": game.id,
        "data": {
            "status": game.status,
            "capacity": game.num_players,
            "players": players
        }
    }

async def _broadcast_lobby_state(game: Game):
    await manager.broadcast_to_game(await _build_lobby_state(game), game.id)

async def _broadcast_player_joined(game_id: str, player_id: str, player_name: str, num_players: int):
    await manager.broadcast_to_game({
        "event": "player_joined",
        "gameId": game_id,
        "data": {
            "playerId": player_id,
            "playerName": player_name,
            "numPlayers": num_players
        }
    }, game_id)

async def delete_player(player_id: str):
    query = delete(players_table).where(players_table.c.id == player_id)
    await database.execute(query)

async def start_game(game_id: str):
    game = await get_game(game_id)
    game.status = GameStatus.PREPARATION.value
    game.current_turn_player = await _determine_first_player(game)
    await save_game(game)

    await manager.broadcast_to_game({
        "event": "game_starting",
        "game_id": game_id,
        "first_player": game.current_turn_player,
        "players_count": game.num_players,
        "message": f"Game {game.nameGame} has started! First turn: {game.current_turn_player}"
    }, game_id)
    
    await manager.broadcast_to_game({
        "event": "preparation_round_started",
        "game_id": game_id,
        "message": "Starting card distribution...",
        "phase": "dealing_cards"
    }, game_id)

def days_to_agatha_birthday(birthdate: date) -> int:
    if not birthdate:
        return 9999
    today_year = datetime.now().year
    agatha = date(today_year, 9, 15)
    player_bd = date(today_year, birthdate.month, birthdate.day)
    diff = abs((player_bd - agatha).days)
    if diff > 182:
        diff = 365 - diff
    return diff

async def _determine_first_player(game: Game):
    agatha_birthday = date(1990, 9, 15)  
    closest_player_id = None
    min_distance = float('inf')
    for player_id in game.players:
        player = await get_player(player_id)
        if player and player.birthdate:
            try:
                birth = datetime.strptime(player.birthdate, "%Y-%m-%d").date()
                player_birthday = birth.replace(year=agatha_birthday.year)
                distance = abs((player_birthday - agatha_birthday).days)
                year_wrap_distance = 365 - distance
                actual_distance = min(distance, year_wrap_distance)
                if actual_distance < min_distance:
                    min_distance = actual_distance
                    closest_player_id = player_id
            except Exception:
                continue
    return closest_player_id or (game.players[0] if game.players else None)

# STORY 16 - Terminar turno 



async def end_turn(game_id: str, player_id: str):
    """
    Finaliza el turno del jugador activo y pasa el turno al siguiente.
    Valida que:
      - El jugador sea el actual.
      - Tenga 6 cartas al terminar.
    """
    game = await get_game(game_id)
    if not game:
        raise ValueError("Game not found")

    if game.current_turn_player != player_id:
        raise PermissionError("Not your turn")

    hand_count = await database.fetch_val(
        select(func.count())
        .select_from(player_hands)
        .where(player_hands.c.game_id == game_id)
        .where(player_hands.c.player_id == player_id)
    )
    if hand_count != 6:
        raise ValueError("Player must end turn with exactly 6 cards")

    if not game.players or len(game.players) == 0:
        raise ValueError("No players found in game")

    current_index = game.players.index(player_id)
    next_index = (current_index + 1) % len(game.players)
    next_player_id = game.players[next_index]

    # Actualizar turno y resetear fase/acción
    await database.execute(
        update(games)
        .where(games.c.id == game_id)
        .values(
            current_turn_player=next_player_id,
            turn_phase=TurnPhase.ACTION,
            last_action=Action.NONE
        )
    )

    await manager.broadcast_to_game({
        "event": "turn_ended",
        "game_id": game_id,
        "previous_player": player_id,
        "next_player": next_player_id,
        "message": f"Turn ended. It's now {next_player_id}'s turn."
    }, game_id)

    return {
        "success": True,
        "game_id": game_id,
        "previous_player": player_id,
        "next_player": next_player_id
    }

# GameService

class GameService:
    async def advance_turn_and_broadcast(self, game_id: str) -> str:
        new_player_id = game_manager.advance_turn_next(game_id)
        event = TurnChangedEvent(game_id=game_id, current_turn_player=new_player_id).dict()
        await manager.broadcast_to_game(event, game_id)
        return new_player_id

game_service = GameService()

async def broadcast_sets_update(game_id: str, sets: list):
    """
    Envía una actualización global por WebSocket a todos los jugadores conectados a la partida.
    Se utiliza cuando se crean o modifican sets de detectives.
    """
    try:
        payload = {
            "event": "sets.updated",
            "game_id": game_id,
            "sets": sets
        }
        await websocket_manager.broadcast_to_game(payload, game_id)
    except Exception as e:
        print(f"[WS] Error broadcasting sets.updated: {e}")