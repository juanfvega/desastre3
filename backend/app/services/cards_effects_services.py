#app/services/cards_effects_services.py
import asyncio
import random
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import insert, select,func, and_, update
from app.core.database import database
from app.models.hand import player_hands
from app.models.detective_sets import detective_sets  # tabla de sets en mesa
from app.models.card import PlayCardRequest
from app.managers.connection_manager import connection_manager
from app.services.card_services import discard_card

# Para ver si la carta es jugable (modificar para futuras cartas)
DETECTIVE_REQUIREMENTS = {
    "detective_poirot": 3,
    "detective_marple": 3,
    "detective_satterthwaite": 3,
    "detective_pyne": 2,
    "detective_brent": 2,
    "detective_tommyberesford": 2,
    "detective_tuppenceberesford": 2,
    "detective_quin": 0,     # comodín de mano
    "detective_oliver": 0,   # comodín de set en mesa
}
async def can_play_card(game_id: str, player_id: str, card_name: str) -> dict:
    """
    Devuelve si la carta se puede jugar:
    - can_play: se puede jugar
    - by_hand: cumple por cartas en mano (incluye comodín Quin)
    - by_table: cumple por set en mesa
    """

    # Traer la carta de la mano del jugador (CASE-INSENSITIVE por name)
    card = await database.fetch_one(
        player_hands.select().where(
            and_(
                player_hands.c.game_id == game_id,
                player_hands.c.player_id == player_id,
                func.lower(player_hands.c.name) == card_name.lower(),
            )
        )
    )

    if not card:
        return {"can_play": False, "by_hand": False, "by_table": False}

    card_type = (card["type"] or "").lower()

    # --- Lógica según tipo ---
    if card_type == "detective":
        required = DETECTIVE_REQUIREMENTS.get(card_name)
        if required is None:
            return {"can_play": False, "by_hand": False, "by_table": False}

        # Contar cartas del mismo nombre en mano (CASE-INSENSITIVE)
        player_cards_same = await database.fetch_all(
            player_hands.select().where(
                and_(
                    player_hands.c.game_id == game_id,
                    player_hands.c.player_id == player_id,
                    func.lower(player_hands.c.name) == card_name.lower(),
                )
            )
        )
        count_same = len(player_cards_same)

        # Contar comodines Quin en mano (CASE-INSENSITIVE)
        player_cards_quin = await database.fetch_all(
            player_hands.select().where(
                and_(
                    player_hands.c.game_id == game_id,
                    player_hands.c.player_id == player_id,
                    func.lower(player_hands.c.name) == "detective_quin",
                )
            )
        )
        count_quin = len(player_cards_quin)

        total_in_hand = count_same + (count_quin if card_name != "detective_oliver" else 0)
        by_hand = (total_in_hand >= required) if card_name != "detective_oliver" else False

        # Verificar sets en mesa (de cualquier jugador) (CASE-INSENSITIVE)
        sets_in_table = await database.fetch_all(
            detective_sets.select().where(
                and_(
                    detective_sets.c.game_id == game_id,
                    func.lower(detective_sets.c.detective_name) == card_name.lower(),
                )
            )
        )
        has_set_on_table = len(sets_in_table) > 0

        # Lógica de table
        if card_name == "detective_quin":
            # según tu comentario original:
            by_table = False  # solo se puede usar en mano
            by_hand = False   # solo se puede jugar en conjunto (se controla en play_card)
        elif card_name == "detective_oliver":
            # comprueba si existe AL MENOS un set en mesa
            any_sets = await database.fetch_all(
                detective_sets.select().where(detective_sets.c.game_id == game_id)
            )
            by_table = len(any_sets) > 0
            by_hand = False  # solo se puede jugar en mesa
        else:
            by_table = has_set_on_table

        can_play = by_hand or by_table
        return {"can_play": can_play, "by_hand": by_hand, "by_table": by_table}

    elif card_type == "event":
        # Lógica futura
        if card_name.lower() == "event_anothervictim":
            
            # Comprobar si existe al menos un set en mesa
            sets_on_table = await database.fetch_all(
                detective_sets.select().where(detective_sets.c.game_id == game_id)
                (detective_sets.c.player_id != player_id)  # excluir sets propios 
            )
            has_sets_on_table = len(sets_on_table) > 0
            
            # Comprobar si el jugador tiene la carta en mano
            card_in_hand = await database.fetch_one(
                select(player_hands).where(
                    (player_hands.c.game_id == game_id) &
                    (player_hands.c.player_id == player_id) &
                    (func.lower(player_hands.c.name) == "event_anothervictim")
                )
            )
            has_card_in_hand = card_in_hand is not None
            
            by_table = has_sets_on_table and has_card_in_hand
            by_hand = has_sets_on_table and has_card_in_hand
            can_play = has_sets_on_table and has_card_in_hand
            
            return {"can_play": can_play, "by_hand": by_hand, "by_table": by_table}
        else:
            return {"can_play": False, "by_hand": False, "by_table": False}

    elif card_type == "instant":
        # Lógica futura
        return {"can_play": False, "by_hand": False, "by_table": False}

    elif card_type == "devious":
        # Lógica futura
        return {"can_play": False, "by_hand": False, "by_table": False}

    else:
        # Tipo desconocido
        return {"can_play": False, "by_hand": False, "by_table": False}
    

async def play_card(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """
    Flujo general para jugar cualquier carta:
    1. Notifica a todos los jugadores que se intentó jugar la carta.
    2. Espera unos segundos para ver si alguien la niega (si aplica).
       - Si es negada, se descarta y termina.
       - Si no es negada, se llama a la función de efecto específica.
    
    (lógica de negación a implementar)
    """

    player_hand = extra_data.player_hand if extra_data else None
    
    # Traer la carta de la mano del jugador (CASE-INSENSITIVE por name)
    card = await database.fetch_one(
        player_hands.select().where(
            and_(
                player_hands.c.game_id == game_id,
                player_hands.c.player_id == player_id,
                func.lower(player_hands.c.name) == card_name.lower(),
            )
        )
    )
    
    if not card:
        return {
            "success": False,
            "error": f"No se encontró en mano la carta '{card_name}' para el jugador {player_id}."
        }

    # Notificar a todos por WS
    await connection_manager.broadcast_to_game({
        "event": "play_card_attempt",
        "game_id": game_id,
        "player_id": player_id,
        "card_name": card_name,
    }, game_id)

    # --- ESPERA PARA NEGACION ---
    NEGATION_TIMEOUT = 5
    negated = False

    # falta implementar la lógica real de negación
    await asyncio.sleep(NEGATION_TIMEOUT)

    if negated:
        await discard_card(game_id, player_id, card_name)
        return {
            "card_name": card_name,
            "player_id": player_id,
            "success": False,
            "negated": True
        }
        
    card_type = (card["type"] or "").lower()
    extra_info = None
    
    # --- SI ES UNA CARTA DETECTIVE ---
    if card_type == "detective":
        # caso crear nuevo set
        if player_hand:
            required_cards = DETECTIVE_REQUIREMENTS.get(card_name, 0)
            if required_cards > 0:
                # Traer detectives del jugador (CASE-INSENSITIVE por type)
                query = select(player_hands).where(
                    and_(
                        player_hands.c.game_id == game_id,
                        player_hands.c.player_id == player_id,
                        func.lower(player_hands.c.type) == "detective",
                    )
                )
                detectives_in_hand = await database.fetch_all(query)

                # Separar detectives del mismo tipo y comodines (CASE-INSENSITIVE por name)
                same_detectives = [d for d in detectives_in_hand if (d["name"] or "").lower() == card_name.lower()]
                jokers = [d for d in detectives_in_hand if (d["name"] or "").lower() == "detective_quin"]
                
                num_same = len(same_detectives)
                num_jokers = len(jokers)
                total_available = num_same + num_jokers

                # Verificar si tiene suficientes detectives (usando comodines si hace falta)
                if total_available < required_cards:
                    return {
                        "success": False,
                        "error": (
                            f"No tienes suficientes detectives ({total_available}/{required_cards}) "
                            f"para jugar {card_name}. Detectives reales: {num_same}, comodines: {num_jokers}"
                        )
                    }

                # --- Seleccionar qué cartas se usarán ---
                selected_cards = []

                # 1. Usar primero detectives del mismo tipo
                selected_cards.extend(same_detectives[:required_cards])

                # 2. Si no alcanza, completar con comodines
                if len(selected_cards) < required_cards:
                    faltan = required_cards - len(selected_cards)
                    selected_cards.extend(jokers[:faltan])

                # --- Crear el nuevo set ---
                cards_used_data = [c["name"] for c in selected_cards]
                await database.execute(insert(detective_sets).values(
                    game_id=game_id,
                    player_id=player_id,
                    detective_name=card_name,
                    set_size=required_cards,
                    cards_used=cards_used_data
                ))

                # --- Eliminar las cartas usadas de la mano ---
                for c in selected_cards:
                    await database.execute(
                        player_hands.delete().where(player_hands.c.id == c["id"])
                    )

                # Notificación del evento:
                await connection_manager.broadcast_to_game({
                    "event": "detective_set_created",
                    "game_id": game_id,
                    "player_id": player_id,
                    "detective_name": card_name,
                    "cards_used": [c["name"] for c in selected_cards]
                }, game_id)
                
                extra_info = {
                    "card_name": card_name,
                    "set_create": True,
                    "game_id": game_id,
                    "player_id": player_id,
                }
                
        #caso de jugar en un set ya exitente
        else:
            #falta impementar ademas me faltaria el dato de en que set se jugo
            return {"success": False, "error": "Jugar sobre un set existente aún no está implementado."}
            

    # --- LLAMADA AL EFECTO SEGÚN NOMBRE DE CARTA ---
    if card_name == "detective_brent":
        result = await effect_detective_brent(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_pyne":
        result = await effect_detective_pyne(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_marple":
        result = await effect_detective_marple(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_quin":
        result = await effect_detective_quin(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_oliver":
        result = await effect_detective_oliver(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_tommyberesford":
        result = await effect_detective_tommyberesford(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_tuppenceberesford":
        result = await effect_detective_tuppenceberesford(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_satterthwaite":
        result = await effect_detective_satterthwaite(game_id, player_id, card_name, extra_data)
    elif card_name == "detective_poirot":
        result = await effect_detective_poirot(game_id, player_id, card_name, extra_data)
    # Instant
    elif card_name == "instant_notsofast":
        result = await effect_instant_notsofast(game_id, player_id, card_name, extra_data)
    # Devious
    elif card_name == "devious_blackmailed":
        result = await effect_devious_blackmailed(game_id, player_id, card_name, extra_data)
    elif card_name == "devious_fauxpas":
        result = await effect_devious_fauxpas(game_id, player_id, card_name, extra_data)
    # Event
    elif card_name == "event_deadcardfolly":
        result = await effect_event_deadcardfolly(game_id, player_id, card_name, extra_data)
    elif card_name == "event_pointsuspicious":
        result = await effect_event_pointsuspicious(game_id, player_id, card_name, extra_data)
    elif card_name == "event_anothervictim":
        result = await effect_event_anothervictim(game_id, player_id, card_name, extra_data)
    elif card_name == "event_lookashes":
        result = await effect_event_lookashes(game_id, player_id, card_name, extra_data)
    elif card_name == "event_cardtrade":
        result = await effect_event_cardtrade(game_id, player_id, card_name, extra_data)
    elif card_name == "event_onemore":
        result = await effect_event_onemore(game_id, player_id, card_name, extra_data)
    elif card_name == "event_earlytrain":
        result = await effect_event_earlytrain(game_id, player_id, card_name, extra_data)
    elif card_name == "event_cardsonthetable":
        result = await effect_event_cardsonthetable(game_id, player_id, card_name, extra_data)
    # Cualquier otra carta
    else:
        result = {
            "card_name": card_name,
            "player_id": player_id,
            "success": True,
            "message": "Carta jugada pero o no existe o no tiene efecto implementado"
        }
    
    # Añadir info adicional antes de devolver
    if isinstance(result, dict):
        if extra_info:
            result.update(extra_info)
        return result
    # si no devuelve dict
    else:
        return {
            "effect_result": result,
            **(extra_info or {})
        }


# --- logica de las funciones ---

# --- Detectives ---
async def effect_detective_brent(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_pyne(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_marple(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_quin(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_oliver(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_tommyberesford(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_tuppenceberesford(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_satterthwaite(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_detective_poirot(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"


# --- Instant ---
async def effect_instant_notsofast(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"


# --- Devious ---
async def effect_devious_blackmailed(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_devious_fauxpas(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"


# --- Event ---
async def effect_event_deadcardfolly(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_event_pointsuspicious(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_event_anothervictim(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """
    Lógica de la carta "Another Victim":
    - Roba un set completo de otro jugador.
    """
    if not extra_data or not extra_data.target_player_id:
        raise HTTPException(status_code=400, detail="Se requiere target_player_id")

    target_id = extra_data.target_player_id

    # Obtener todos los sets del objetivo
    target_sets_rows = await database.fetch_all(
        select(detective_sets).where(
            (detective_sets.c.game_id == game_id) &
            (detective_sets.c.player_id == target_id)
        )
    )

    if not target_sets_rows:
        # El objetivo no tiene sets
        result = {
            "success": False,
            "message": f"{target_id} no tiene sets para robar",
            "attacker_id": player_id,
            "target_id": target_id,
            "cards_discarded": [card_name]
        }
        
        # Broadcast a todos los jugadores
        await connection_manager.broadcast_to_game({
            "event": "rob_set_result",
            "game_id": game_id,
            "success": False,
            "message": result.message,
            "attacker_id": attacker_id,
            "target_id": target_id,
            "cards_discarded": ["Another Victim"]
        }, game_id)
    
        return result

    # Seleccionar un set aleatorio (ya que no hay seleccion especifica en el original)
    robbed_set = random.choice(target_sets_rows)

    # Transferir el set al atacante
    attacker_id = player_id
    await database.execute(
        update(detective_sets)
        .where(detective_sets.c.id == robbed_set["id"])
        .values(player_id=attacker_id)
    )
    
    # Broadcast a todos los jugadores
    await connection_manager.broadcast_to_game({
        "event": "rob_set_result",
        "game_id": game_id,
        "success": True,
        "message": f"{player_id} robó el set '{robbed_set['detective_name']}' de {target_id}",
        "set_robbed": robbed_set["detective_name"],
        "attacker_id": attacker_id,
        "target_id": target_id,
        "cards_discarded": [card_name]
    }, game_id)

    return {
        "success": True,
        "message": f"{player_id} robó el set '{robbed_set['detective_name']}' de {target_id}",
        "set_robbed": robbed_set["detective_name"],
        "attacker_id": player_id,
        "target_id": target_id,
        "cards_discarded": [card_name]
    }

async def effect_event_lookashes(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_event_cardtrade(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_event_onemore(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_event_earlytrain(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"

async def effect_event_cardsonthetable(game_id: str, player_id: str, card_name: str, extra_data: Optional[PlayCardRequest] = None):
    """Lógica a implementar"""
    return "ok"