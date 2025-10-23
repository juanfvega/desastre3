import React from "react";
import "./EndGameModal.css";
import { useNavigate } from "react-router-dom";

const EndGameModal = ({ isOpen, winnerName, onClose }) => {
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleClose = () => {
    onClose();
    navigate("/games"); // Redirige al listado de partidas
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content game-end-modal">
        <h2>🕵️‍♂️ ¡El asesino ha escapado!</h2>
        <p>La partida ha terminado.</p>
        {winnerName && (
          <p>
            <strong>Ganador:</strong> {winnerName}
          </p>
        )}
        <button onClick={handleClose} className="game-button">
          Salir
        </button>
      </div>
    </div>
  );
}

export default EndGameModal;