import random
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from app.core.database import database
from sqlalchemy import select, delete, update, func
from app.models.detective_sets import detective_sets
from app.services import game_service
from app.managers.connection_manager import manager
from app.models.game import Action, GameStatus, TurnPhase, games
from app.models.deck import deck_cards
from app.schemas.game_schema import PreparationRoundResponse
from app.models.hand import player_hands 
from app.models.player import players_table

REQUIRED_CARDS = 6
REQUIRED_SECRETS = 3
SPECIAL_CARD_NAME = "instant_notsofast"

async def initialize_deck(game_id: str):
    """
    Inicializa el mazo de cartas para una partida.
    Verifica si ya existe antes de crear uno nuevo.
    """
    print(f"[init deck] game_id={game_id} (tipo {type(game_id)})")
    
    # Obtener el juego
    query = select(games).where(games.c.id == game_id)
    game = await database.fetch_one(query)
    
    if game["deck_initialized"]:
        print(f"Mazo ya inicializado para game_id={game_id}")
        return  # <--- SALIDA si ya estaba inicializado

    # Limpieza previa
    deleted_deck = await database.execute(
        "DELETE FROM deck_cards WHERE game_id = :gid", {"gid": game_id}
    )
    deleted_hands = await database.execute(
        "DELETE FROM player_hands WHERE game_id = :gid", {"gid": game_id}
    )

    print(f"[init deck] Limpieza previa: {deleted_deck} cartas de mazo, {deleted_hands} manos eliminadas")

    # Importar BASE_CARDS desde game_service
    from app.services.game_service import BASE_CARDS
    
    # Crear las cartas e insertarlas en la base de datos
    cards_to_insert = []
    for card_info in BASE_CARDS:
        for _ in range(card_info["amount"]):
            cards_to_insert.append({
                "game_id": game_id,
                "type": card_info["type"],
                "name": card_info["name"],
                "in_deck": 1,  
                "in_card_draft": 0 
            })
    
    if cards_to_insert:
        insert_query = deck_cards.insert()
        await database.execute_many(insert_query, cards_to_insert)
    
    # Marcar mazo como inicializado
    await database.execute(
        games.update().where(games.c.id == game_id).values(deck_initialized=True)
    )
    print(f"[init deck] Flag deck_initialized seteado en True para game_id={game_id}")

async def get_player_hand_with_images(player_id: str):

    
    query = select(player_hands).where(player_hands.c.player_id == player_id)
    rows = await database.fetch_all(query)
    
    cards_list = []
    for row in rows:
        image_id_from_name = row["name"] 
        
        cards_list.append({
            "id": row["id"],      
            "type": row["type"], 
            "name": image_id_from_name, 
            "image_id": image_id_from_name 
        })
    
    return cards_list

async def prepare_piles(game_id: str):
    # Obtenemos las cartas del mazo que siguen disponibles
    query = select(deck_cards).where(
        (deck_cards.c.game_id == game_id) & 
        (deck_cards.c.in_deck == 1)
    ).order_by(func.random())
    rows = await database.fetch_all(query)
    if not rows:
        return

    # Convertir a lista para poder trabajar con índices
    available_cards = list(rows)
    
    # Primera carta disponible → descarte
    if len(available_cards) >= 1:
        discard_card = available_cards[0]
        query = update(deck_cards).where(deck_cards.c.id == discard_card.id).values(
            in_deck=0, in_card_draft=0
        )
        await database.execute(query)
        discard_pile = {"type": discard_card.type, "name": discard_card.name}
    else:
        discard_pile = None

    # Siguientes 3 cartas disponibles → card draft
    card_draft = []
    for i in range(1, min(4, len(available_cards))):
        draft_card = available_cards[i]
        query = update(deck_cards).where(deck_cards.c.id == draft_card.id).values(
            in_deck=None, in_card_draft=1  
        )
        await database.execute(query)
        await broadcast_deck_state(game_id)
        card_draft.append({"type": draft_card.type, "name": draft_card.name})

    # Contar cartas restantes en el mazo (las que siguen con in_deck=1)
    remaining_query = select(deck_cards).where(
        (deck_cards.c.game_id == game_id) & 
        (deck_cards.c.in_deck == 1)  
    )
    remaining_rows = await database.fetch_all(remaining_query)
    deck_count = len(remaining_rows)

    # Broadcast de actualización
    await manager.broadcast_to_game({
        "event": "deck_update",
        "game_id": game_id,
        "draw_pile_count": deck_count,
        "top_discard": {"type": discard_pile["type"], "name": discard_pile["name"]} if discard_pile else None,
        "card_draft": [{"type": card["type"], "name": card["name"]} for card in card_draft],
    }, game_id)


async def deal_cards_round_robin(game_id: str):
    """
    Reparte cartas a todos los jugadores de manera round-robin:
      - 1 carta especial "instant_notsofast" por jugador
      - 5 cartas adicionales por jugador
    Actualiza las manos de los jugadores, el mazo y el card draft.
    """
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    player_ids: List[str] = game.players or []
    if not player_ids:
        raise HTTPException(status_code=400, detail="No players to deal")
    
    # Traer todas las cartas actualmente en el mazo
    deck_rows = await database.fetch_all(
        select(deck_cards.c.id, deck_cards.c.type, deck_cards.c.name)
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == 1) 
    )

    if not deck_rows:
        raise HTTPException(status_code=400, detail="No cards left in deck")

    # Separar cartas especiales de las normales
    special_cards = [c for c in deck_rows if c["name"] == SPECIAL_CARD_NAME]
    other_cards = [c for c in deck_rows if c["name"] != SPECIAL_CARD_NAME]

    # Validaciones
    if len(special_cards) < len(player_ids):
        raise HTTPException(
            status_code=400,
            detail=f"Not enough '{SPECIAL_CARD_NAME}' cards to deal to all players"
        )

    needed_other = (REQUIRED_CARDS - 1) * len(player_ids)
    available_for_dealing = len(other_cards) + (len(special_cards) - len(player_ids))
    if available_for_dealing < needed_other:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough cards to deal {REQUIRED_CARDS - 1} additional cards per player "
                   f"(need {needed_other}, found {available_for_dealing})"
        )

    # Ejecutar todo en una transacción para consistencia
    async with database.transaction():
        # 1) Limpiar manos y resetear mazo
        await database.execute(
            "DELETE FROM player_hands WHERE game_id = :gid",
            {"gid": game_id}
        )
        await database.execute(
            "UPDATE deck_cards SET in_deck = 1, in_card_draft = 0 WHERE game_id = :gid",  
            {"gid": game_id}
        )

        # 2) Repartir 1 carta especial "instant_notsofast" por jugador
        for pid in player_ids:
            card = special_cards.pop()
            await database.execute(
                """
                INSERT INTO player_hands (game_id, player_id, type, name)
                VALUES (:gid, :pid, :type, :name)
                """,
                {"gid": game_id, "pid": pid, "type": card["type"], "name": card["name"]}
            )
            await database.execute(
                delete(deck_cards).where(deck_cards.c.id == card["id"])
            )

        # 3) Repartir 5 cartas adicionales por jugador (round-robin)

            # --- fin del bloque async with database.transaction() ---

        remaining_cards = other_cards + special_cards
        random.shuffle(remaining_cards)
        idx = 0
        for _ in range(REQUIRED_CARDS - 1):  # 5 rondas
            for pid in player_ids:
                card = remaining_cards[idx]
                await database.execute(
                    """
                    INSERT INTO player_hands (game_id, player_id, type, name)
                    VALUES (:gid, :pid, :type, :name)
                    """,
                    {"gid": game_id, "pid": pid, "type": card["type"], "name": card["name"]}
                )
                await database.execute(
                    delete(deck_cards).where(deck_cards.c.id == card["id"])
                )
                idx += 1


    # 4) Broadcast resumen de cartas por jugador
    summary = []
    for pid in player_ids:
        row = await database.fetch_one(
            "SELECT COUNT(*) as cnt FROM player_hands WHERE game_id=:gid AND player_id=:pid",
            {"gid": game_id, "pid": pid},
        )
        count = row["cnt"] if row else 0
        summary.append({"player_id": pid, "hand_count": count})

    await manager.broadcast_to_game(
        {
            "event": "cards_dealt",
            "game_id": game_id,
            "summary": summary,
        },
        game_id
    )

    # 5) Actualizar pila de descarte y card draft desde el mazo actual
    await prepare_piles(game_id)

    # 6) Finalizar automáticamente la ronda de preparación
    await finalize_preparation_round(game_id)


async def finalize_preparation_round(game_id: str) -> PreparationRoundResponse:
    # Obtener el juego
    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if getattr(game, "status", None) != GameStatus.PREPARATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game must be in preparation to finalize preparation"
        )

    player_ids: List[str] = game.players or []
    if not player_ids:
        raise HTTPException(status_code=400, detail="No players in the game")

    # Validar que todos los jugadores tengan exactamente 6 cartas
    missing_data = []
    for pid in player_ids:
        row = await database.fetch_one(
            "SELECT COUNT(*) as cnt FROM player_hands WHERE game_id=:gid AND player_id=:pid",
            {"gid": game_id, "pid": pid},
        )
        count = row["cnt"] if row else 0
        if count != REQUIRED_CARDS:
            missing_data.append(f"Player {pid} must have {REQUIRED_CARDS} cards (has {count})")

    # Validar estado de discard pile y card draft
    discard_row = await database.fetch_one(
        select(deck_cards).where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == 0)  
        .where(deck_cards.c.in_card_draft == 0)
    )
    draft_rows = await database.fetch_all(
        select(deck_cards).where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck.is_(None))
        .where(deck_cards.c.in_card_draft == 1)  
    )

    if not discard_row:
        missing_data.append("Discard pile is missing its top card")
    if len(draft_rows) < 3:
        missing_data.append("Card draft must contain at least 3 cards")

    # Si hay problemas, devolver respuesta fallida
    if missing_data:
        return PreparationRoundResponse(
            success=False,
            game_id=game_id,
            preparation_round_finished=False,
            issues=missing_data,
            message="Preparation round validation failed"
        )

    # Marcar preparación como finalizada en la tabla games
    await database.execute(
        update(games)
        .where(games.c.id == game_id)
        .values(status=GameStatus.PLAYING)
    )

    # Notificar a todos los jugadores
    await manager.broadcast_to_game({
        "event": "preparation_round_ended",
        "game_id": game_id,
        "message": "Preparation round completed. Game is ready to begin!",
        "players_ready": len(player_ids),
        "next_phase": "game_play",
    }, game_id)

    return PreparationRoundResponse(
        success=True,
        game_id=game_id,
        preparation_round_finished=True,
        next_phase="game_play",
        message="Preparation round completed successfully"
    )


async def draw_cards(game_id: str, player_id: str, count: int) -> List[dict]:
    """
    Permite a un jugador robar cartas del mazo.
    Actualiza la mano del jugador y el mazo.
    """
    if count <= 0:
        raise HTTPException(status_code=400, detail="Count must be positive")

    game = await game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if player_id not in (game.players or []):
        raise HTTPException(status_code=403, detail="Player not in this game")

    # Traer cartas disponibles en el mazo
    deck_rows = await database.fetch_all(
        select(deck_cards).where(
            (deck_cards.c.game_id == game_id) &
            (deck_cards.c.in_deck == 1)
        ).order_by(deck_cards.c.id.asc())
    )
    random.shuffle(deck_rows) #cartas en orden azar

    if not deck_rows:
        raise HTTPException(status_code=400, detail="No cards left in deck")

    if len(deck_rows) < count:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough cards to draw {count} (only {len(deck_rows)} left)"
        )
    # Robar cartas 
    drawn_cards = deck_rows[:count]

    async with database.transaction():
        # Insertar cartas en la mano del jugador y removerlas del mazo
        for card in drawn_cards:
            
            await database.execute(
                """
                INSERT INTO player_hands (game_id, player_id, type, name)
                VALUES (:gid, :pid, :type, :name)
                """,
                {"gid": game_id, "pid": player_id, "type": card.type, "name": card.name}
            )
            await database.execute(
                delete(deck_cards).where(deck_cards.c.id == card.id)
            )
    # actualizar cantidad restante en el mazo
    broadcast_data = {
        "event": "deck_updated",
        "payload": {
            "regularCount": len(deck_rows) - count
        }
    }
    await manager.broadcast_to_game(broadcast_data, game_id)

    return [{"id": card.id, "type": card.type, "name": card.name} for card in drawn_cards]

async def refill_card_draft(game_id: str):
    """
    Función auxiliar para rellenar el card draft con cartas del mazo.
    """
    
    # 1. Contar cuántas cartas hay actualmente en el draft
    draft_rows = await database.fetch_all(
        select(deck_cards.c.id).where(
            (deck_cards.c.game_id == game_id) & 
            (deck_cards.c.in_card_draft == 1) 
        )
    )
    current_draft_count = len(draft_rows)
    needed = 3 - current_draft_count
    
    if needed <= 0:
        return # Draft ya lleno o tiene suficientes

    # 2. Tomar cartas del mazo regular (in_deck=1)
    new_draft_rows = await database.fetch_all(
        select(deck_cards).where(
            (deck_cards.c.game_id == game_id) & 
            (deck_cards.c.in_deck == 1)
        ).order_by(func.random()).limit(needed) # Toma solo las que faltan
    )
    
    if not new_draft_rows:
        return # No hay más cartas en el mazo

    # 3. Mover las nuevas cartas del mazo al draft
    for card in new_draft_rows:
        await database.execute(
            update(deck_cards).where(deck_cards.c.id == card.id).values(
                in_deck=None, in_card_draft=1 
            )
        )
        
    print(f"[Draft] Se rellenaron {len(new_draft_rows)} cartas al draft.")
    
# ----------------------------------------------------------------------
    
async def draft_card_to_hand(game_id: str, player_id: str, card_name: str):
    """
    Mueve una carta del card draft a la mano del jugador y actualiza el draft.
    """
    game = await game_service.get_game(game_id)
    
    # 1. Verificar el límite de mano (Menos de 6)
    row = await database.fetch_one(
        "SELECT COUNT(*) as cnt FROM player_hands WHERE game_id=:gid AND player_id=:pid",
        {"gid": game_id, "pid": player_id},
    )
    hand_count = row["cnt"] if row else 0
    
    if hand_count >= 6:
         raise HTTPException(status_code=400, detail=f"No puedes tomar del draft, tu mano está llena ({hand_count} cartas).")


    async with database.transaction():
        # A. Localizar y eliminar la carta del draft (deck_cards.in_card_draft = 1)
        draft_card_row = await database.fetch_one(
            select(deck_cards).where(
                (deck_cards.c.game_id == game_id) &
                (deck_cards.c.name == card_name) &
                (deck_cards.c.in_card_draft == 1)
            ).order_by(deck_cards.c.id.asc())
        )
        
        if not draft_card_row:
            raise HTTPException(status_code=404, detail=f"Carta '{card_name}' no encontrada en el draft.")
            
        draft_card_id = draft_card_row["id"]
        
        # Eliminar del deck_cards (el draft es una zona, no un descarte)
        await database.execute(
            delete(deck_cards).where(deck_cards.c.id == draft_card_id)
        )
        
        # B. Insertar la carta en la mano del jugador
        await database.execute(
            player_hands.insert().values(
                game_id=game_id, 
                player_id=player_id, 
                type=draft_card_row["type"], 
                name=draft_card_row["name"]
            )
        )
        
        # C. Rellenar el draft
        await refill_card_draft(game_id)
        
        # D. Preparar el broadcast (Actualizar info del mazo y draft)
        await broadcast_deck_state(game_id) # Usamos prepare_piles para hacer el broadcast de deck_update
    
    return {"success": True, "card_name": card_name}

#13-----
async def broadcast_deck_state(game_id: str):
    """
    Consulta el estado actual del mazo, descarte y draft,
    y lo notifica a todos los jugadores de la partida.
    """
    # Contar cartas restantes en el mazo (draw pile)
    deck_count_query = select(func.count(deck_cards.c.id)).where(
        (deck_cards.c.game_id == game_id) & (deck_cards.c.in_deck == 1)
    )
    deck_count = await database.fetch_val(deck_count_query)

    # Obtener la carta superior del descarte
    top_discard_query = select(deck_cards).where(
        (deck_cards.c.game_id == game_id) &
        (deck_cards.c.in_deck == 0)
    ).order_by(deck_cards.c.id.desc()).limit(1) # Ordenar por ID descendente para obtener la última
    discard_card = await database.fetch_one(top_discard_query)
    top_discard_data = {"type": discard_card["type"], "name": discard_card["name"]} if discard_card else None

    # Obtener las cartas actuales en el draft
    card_draft_query = select(deck_cards).where(
        (deck_cards.c.game_id == game_id) &
        (deck_cards.c.in_card_draft == 1)
    )
    draft_rows = await database.fetch_all(card_draft_query)
    card_draft_data = [{"type": card["type"], "name": card["name"]} for card in draft_rows]

    # Enviar la actualización a todos los jugadores
    await manager.broadcast_to_game({
        "event": "deck_update",
        "game_id": game_id,
        "draw_pile_count": deck_count,
        "top_discard": top_discard_data,
        "card_draft": card_draft_data,
    }, game_id)
async def discard_card(game_id: str, player_id: str, card_name: str):
    """
    Descarta una carta de la mano del jugador usando game_id, player_id y card_name.

    - Busca una instancia de la carta en player_hands.
    - La elimina de la mano del jugador.
    - La inserta en deck_cards como descarte (in_deck=0, in_card_draft=0).
    
    """

    # 1. Buscar una carta válida en la mano del jugador
    query_hand = """
        SELECT id, type, name FROM player_hands
        WHERE game_id = :gid
          AND player_id = :pid
          AND name = :cname
        LIMIT 1
    """
    hand_card = await database.fetch_one(query_hand, {
        "gid": game_id,
        "pid": player_id,
        "cname": card_name
    })

    if not hand_card:
        raise ValueError(f"No se encontró '{card_name}' en la mano del jugador {player_id}.")

    # 2. Eliminar la carta de la mano
    query_delete = "DELETE FROM player_hands WHERE id = :cid"
    await database.execute(query_delete, {"cid": hand_card["id"]})

    # 3. Insertar la carta nuevamente en deck_cards, marcada como descarte
    query_insert_discard = """
        INSERT INTO deck_cards (game_id, type, name, in_deck, in_card_draft)
        VALUES (:gid, :ctype, :cname, 0, 0)
    """
    await database.execute(query_insert_discard, {
        "gid": game_id,
        "ctype": hand_card["type"],
        "cname": hand_card["name"]
    })
    
    top_discard = {
        "type": hand_card["type"],
        "name": hand_card["name"],
    }
    await broadcast_deck_state(game_id)

    # 5. Devolver confirmación
    return {
        "success": True,
        "game_id": game_id,
        "discarded_card": card_name,
        "top_discard": top_discard,
    }
#-------

async def get_detective_sets_by_game(game_id: str) -> Dict[str, list]:
    """
    Devuelve los sets de detectives organizados por jugador.
    Cada jugador tendrá una lista de sets, y cada set tiene las cartas usadas.
    Si el primer nombre de la lista es 'detective_quin' o 'detective_oliver', se mueve al final.
    """
    sets_in_game = await database.fetch_all(
        detective_sets.select().where(detective_sets.c.game_id == game_id)
    )

    result: Dict[str, list] = {}

    for s in sets_in_game:
        # Traer el nombre del jugador (desde players)
        player = await database.fetch_one(
            players_table.select().where(players_table.c.id == s["player_id"])
        )
        player_name = player["username"] if player else s["player_id"]

        # Preparar la lista de cartas usadas
        cards_list = [{"name": name} for name in s["cards_used"]]

        # Reordenar si el primer elemento es comodín
        if cards_list and cards_list[0]["name"] in ["detective_quin", "detective_oliver"]:
            cards_list.append(cards_list.pop(0))

        # Añadir el set al jugador correspondiente
        if player_name not in result:
            result[player_name] = []

        result[player_name].append({"cards": cards_list})

    return result