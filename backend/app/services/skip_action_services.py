#skip_action_services.py
import random
from fastapi import HTTPException
from app.core.database import database
from app.models.hand import player_hands
from app.models.deck import deck_cards
from sqlalchemy import select, func


async def skip_discard_and_draw(game_id: str, player_id: str, require_card_in_hand: bool = False):
    """
    Lógica específica para 'No ejecutar acción' (skip):
      1) Descarta UNA carta aleatoria de la mano del jugador al descarte.
      2) Roba UNA carta del mazo principal 
     - require_card_in_hand: si True, lanza 409 si el jugador no tiene cartas para descartar.
      Si False, si no hay cartas, simplemente intenta robar 1.
    """
    async with database.transaction():
        hand_rows = await database.fetch_all(
            player_hands.select().where(
                (player_hands.c.game_id == game_id) & (player_hands.c.player_id == player_id)
            )
        )
        hand = list(hand_rows)

        discarded = None
        drawn = None

        # descartar una al azar
        if not hand:
            if require_card_in_hand:
                raise HTTPException(status_code=409, detail="No cards in hand to discard on skip-action.")
        else:
            to_discard = random.choice(hand)
            # insert en descarte (in_deck=False)
            await database.execute(
                deck_cards.insert().values(
                    game_id=game_id,
                    type=to_discard["type"],
                    name=to_discard["name"],
                    in_deck=False
                )
            )
            # eliminar de la mano
            await database.execute(
                player_hands.delete().where(player_hands.c.id == to_discard["id"])
            )
            discarded = {"type": to_discard["type"], "name": to_discard["name"]}

        # roba carta del mazo principal 
        deck_top = await database.fetch_one(
            deck_cards.select()
            .where((deck_cards.c.game_id == game_id) & (deck_cards.c.in_deck == True))
            .order_by(func.random())  # 👈 selecciona una carta aleatoria
            .limit(1)
        )
        if deck_top:
            # agregar a la mano del jugador
            await database.execute(
                player_hands.insert().values(
                    game_id=game_id,
                    player_id=player_id,
                    type=deck_top["type"],
                    name=deck_top["name"]
                )
            )
            # marcar carta como retirada del mazo
            await database.execute(
                deck_cards.update()
                .where(deck_cards.c.id == deck_top["id"])
                .values(in_deck=False)
            )
            drawn = {"type": deck_top["type"], "name": deck_top["name"]}

        # recuento final de la mano

        final_count = await database.fetch_val(
            select(func.count())
            .select_from(player_hands)
            .where(
                (player_hands.c.game_id == game_id) &
                (player_hands.c.player_id == player_id)
            )
        )

        # Calcular draw_pile_count y top_discard
        draw_pile_count = await database.fetch_val(
            select(func.count())
            .select_from(deck_cards)
            .where((deck_cards.c.game_id == game_id) & (deck_cards.c.in_deck == True))
        ) or 0

        top_discard = discarded  # La carta recién descartada es la cima del descarte

    return {
        "discarded": discarded,
        "drawn": drawn,
        "final_hand_count": int(final_count or 0),
        "draw_pile_count": draw_pile_count,
        "top_discard": top_discard,
    }