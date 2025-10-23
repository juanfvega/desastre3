import React, { useEffect, useState } from "react";
import  {createHttpService}  from "../services/HttpService";


const EndTurnButton = ({ handCompleted, 
                        setCurrentTurn,
                        currentPlayerPlayEvent,
                        currentPlayerPlaySet,
                        currentPlayerAddOneDetectiveCard,
                        playerId,
                        gameId,
                        isMyTurn,
                        wsService, // <-- nueva prop
                        className=""
                      }) => {

  const httpService = createHttpService();


  useEffect(() => {
    if (!gameId || !playerId || !wsService) return;
    // Suscribirse a eventos relevantes
    const handleEventTurnEnd = async (payload) => {
      //console.log("<event handleEventTurnEnd data es> :", payload);
      if(payload.event === "turn_ended"){
  
        setCurrentTurn(payload.next_player);
      }
    }
    wsService.on("turn_ended", handleEventTurnEnd);
    return () => wsService.off("turn_ended", handleEventTurnEnd);
  }, [gameId, playerId, setCurrentTurn, wsService]);


  // Función HandlerEndTurn del botón
  const handleEndTurn = () => {
  httpService.EndTurn(gameId, playerId)
        .then(response => {
            console.log("handleEndTurn: turno terminado con éxito:", response);
            // Aquí puedes actualizar el estado del juego si es necesario
        })
        .catch(error => {
            console.error("Error al terminar el turno:", error);
        });
        
  };
  // Renderizado condicional: solo mostrar si es el turno del jugador actual
  if (!isMyTurn) return null;
  return (
    <div className="end-turn-container">
      <button
        onClick={handleEndTurn}
        className={isMyTurn ? `${className}` : `${className} disabled`}
        // Esto hará que el botón sea realmente no clickeable cuando buttonEnabled sea false.
        disabled={!isMyTurn}
      >
        Terminar turno
      </button>
    </div>
  );
};


export default EndTurnButton;
