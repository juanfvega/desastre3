import React, { useEffect, useState } from "react";
import {createHttpService} from "../../services/HttpService";
import CardsModal from "../../components/CardModal";

const WatchDiscardPile = ({ cards, showModal, setShowModal, gameData, player, setCards }) => {
    const httpService = createHttpService();

  // Nueva acción al hacer click en una carta
  const handleCardClick = async (card) => {
    try {
      console.log("en handleCardClick se selecciona:", card);
      // Llama al servicio para enviar la carta seleccionada
      const response = await httpService.postSelectedCard(gameData.game_id, player.player_id, card.id);

      if (response) {        
        console.log("Respuesta de postSelectedCard:", response);
        // Recargar las cartas después de enviar la carta seleccionada
        httpService.getCards(player.player_id, gameData.game_id)
          .then(cards => {
            // Actualiza el estado con las cartas obtenidas para el Ingame
            // esta funcion proviene de ingame.jsx setCards
            console.log("en GetCards en WatchDiscardPile :Cartas recargadas después de seleccionar:", cards);
             setCards(cards);
          })
          // Maneja errores en la obtención de cartas
        .catch(error => console.error("Error al obtener cartas después de seleccionar:", error));
        }
    // catch errores en la selección de carta
    } catch (error) {
      console.error("Error al seleccionar carta:", error);
    }

  };

  return (
    <div className="flex flex-col items-center" data-testid="cards-modal">
        <CardsModal
          Cards={cards}
          onClose={() => setShowModal(false)}
          // se pasa la función para manejar el click en la carta
          // luego la recibe Cards y luego CardDetailModal
          isOpen={showModal}
          selectedDiscardPileCard={handleCardClick} // se pasa la acción
        />
    </div>
  );
};

export default WatchDiscardPile;
