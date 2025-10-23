import random
from app.core.database import database
from app.models.hand import player_hands
from app.models.deck import deck_cards


async def auto_discard_if_needed(game_id: str, player_id: str):
    """
    STORY 15 - Descarte automático.
    Aplica las reglas DOTC al finalizar turno:
      - Si tiene >6 cartas: descarta aleatoriamente hasta quedar con 6.
      - Si tiene =6 cartas: descarta 1 y roba 1.
      - Si tiene <6 cartas: roba hasta tener 6.
    """
    # 🔹 Obtener cartas del jugador
    query = player_hands.select().where(player_hands.c.player_id == player_id)
    hand = await database.fetch_all(query)
    num_cards = len(hand)

    discarded = []
    drawn = []

    # --- CASO 1: más de 6 cartas ---
    if num_cards > 6:
        to_discard = num_cards - 6
        cards_to_discard = random.sample(hand, to_discard)

        for card in cards_to_discard:
            # 🔸 Insertar la carta descartada en el mazo de descarte (in_deck=False)
            await database.execute(
                deck_cards.insert().values(
                    game_id=game_id,
                    type=card["type"],
                    name=card["name"],
                    in_deck=False  # 0 = en descarte
                )
            )
            # 🔸 Eliminar de la mano
            await database.execute(
                player_hands.delete().where(player_hands.c.id == card["id"])
            )
            discarded.append({"type": card["type"], "name": card["name"]})

    # --- CASO 2: exactamente 6 cartas ---
    elif num_cards == 6:
        card_to_discard = random.choice(hand)

        # 🔸 Insertar carta descartada en deck_cards (visible en descarte)
        await database.execute(
            deck_cards.insert().values(
                game_id=game_id,
                type=card_to_discard["type"],
                name=card_to_discard["name"],
                in_deck=False
            )
        )

        # 🔸 Eliminar de la mano
        await database.execute(
            player_hands.delete().where(player_hands.c.id == card_to_discard["id"])
        )

        discarded.append(
            {"type": card_to_discard["type"], "name": card_to_discard["name"]}
        )

        # 🔸 Robar una nueva carta del mazo
        new_card = await draw_one_card(game_id, player_id)
        if new_card:
            drawn.append(new_card)

    # --- CASO 3: menos de 6 cartas ---
    elif num_cards < 6:
        missing = 6 - num_cards
        for _ in range(missing):
            new_card = await draw_one_card(game_id, player_id)
            if new_card:
                drawn.append(new_card)

    return {
        "discarded": discarded,
        "drawn": drawn,
        "final_hand_count": num_cards - len(discarded) + len(drawn),
    }


async def draw_one_card(game_id: str, player_id: str):
    """
    Roba una carta del mazo principal (in_deck=True) y la agrega a la mano del jugador.
    Marca la carta como removida del mazo (in_deck=False).
    """
    # Buscar una carta disponible en el mazo
    query = (
        deck_cards.select()
        .where(deck_cards.c.game_id == game_id)
        .where(deck_cards.c.in_deck == True)
        .limit(1)
    )
    card = await database.fetch_one(query)
    if not card:
        return None

    # Insertar la carta en la mano (sin copiar el id del mazo)
    await database.execute(
        player_hands.insert().values(
            game_id=game_id,
            player_id=player_id,
            type=card["type"],
            name=card["name"]
        )
    )

    # Marcar la carta como removida del mazo (ya no está disponible)
    await database.execute(
        deck_cards.update()
        .where(deck_cards.c.id == card["id"])
        .values(in_deck=False)
    )

    # Devolvemos la carta robada (solo para saber cuál fue)
    return {"type": card["type"], "name": card["name"]}
