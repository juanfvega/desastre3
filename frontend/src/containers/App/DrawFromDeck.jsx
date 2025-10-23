// src/components/DrawFromDeck.jsx
// Componente para robar una carta del mazo
// Usa un servicio HTTP para interactuar con el backend
// y actualiza la mano del jugador en el estado local

import React from "react";
import { createHttpService } from "../../services/HttpService";

const DrawFromDeck = ({ playerId, gameId , onDrawSuccess }) => {
	// Manejar el clic en el botón
	const httpService = createHttpService();


const handleDrawFromPile = async () => {
  console.log("handleDrawFromPile called");
  try {
    const response = await httpService.drawCardFromDeck(gameId, playerId);
    console.log("Carta robada:", response);
    if (onDrawSuccess) {
      console.log("Llamando onDrawSuccess desde DrawFromDeck");
      onDrawSuccess(playerId, gameId);
    }
  } catch (error) {
    console.error("Error al robar carta:", error);
  }
};



  return (
    <div>
      <button className="game-button game-button-no-action" onClick={handleDrawFromPile}>
        Robar del mazo
      </button>
    </div>
  );
};

export default DrawFromDeck;
