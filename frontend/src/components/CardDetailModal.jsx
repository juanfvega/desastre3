// src/components/CardDetailModal.jsx
import React from "react";
import "./CardDetailModal.css";
import { createHttpService } from "../services/HttpService";

const http = createHttpService();

/**
 * CardDetailModal unificado:
 * - Mantiene compatibilidad con dev (manejo de look into ashes, descartar, selectedDiscardPileCard, etc.)
 * - Añade soporte para `children` (p.ej. botón "Jugar set")
 * - Maneja onUsedAction y onDiscardAction opcionales (como en mergep0)
 */
const CardDetailModal = ({
  isOpen,
  onClose,
  card,

  // props de dev
  onClickLookIntoAshes,
  onDiscardAction,
  selectedDiscardPileCard,
  setCards,
  gameData,
  player,

  // props de mergep0
  onUsedAction,

  // extensiones
  children,
}) => {
  if (!isOpen || !card) return null;

  const imageId = card.image_id || card.name;
  if (!imageId) return null;
  const imagePath = `/Cards/${imageId}.png`;

  const handleClick = (card) => {
    // Mantiene la lógica de dev para event_lookashes
    if (card.name === "event_lookashes" && onClickLookIntoAshes) {
      http
        .discardCard(gameData?.game_id, player?.player_id, card.name)
        .then(() => console.log("Carta descartada:", card.name))
        .catch((error) =>
          console.error("Error al descartar la carta:", error)
        );

      onClickLookIntoAshes(card);
      onClose?.();
    }

    if (selectedDiscardPileCard) {
      selectedDiscardPileCard(card);
      onClose?.();
    }

    if (onUsedAction) {
      onUsedAction(card);
    }
  };

  const handleDiscard = (card) => {
    // Si se pasa onDiscardAction, llamarlo
    if (onDiscardAction) onDiscardAction(card);
  };

  return (
    <div className="card-detail-overlay" onClick={onClose}>
      <div
        className="card-detail-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Imagen principal */}
        <div className="card-detail-image-wrapper">
          <img
            src={imagePath}
            alt={`Carta ${imageId}`}
            className="card-detail-image"
            onError={(e) => {
              e.currentTarget.style.visibility = "hidden";
              e.currentTarget.setAttribute("aria-hidden", "true");
            }}
          />
        </div>

        {/* Botones estándar */}
        <div
          className="card-detail-buttons"
          style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
        >
          <button
            onClick={() => handleClick(card)}
            className="detail-button Usar"
          >
            Usar
          </button>

          {typeof onDiscardAction === "function" && (
            <button
              onClick={() => handleDiscard(card)}
              className="detail-button Descartar"
            >
              Descartar
            </button>
          )}
        </div>

        {/* Children opcional: para botones extra como “Jugar set” */}
        {children && (
          <div className="card-detail-extra" style={{ marginTop: 10 }}>
            {children}
          </div>
        )}
      </div>
    </div>
  );
};

export default CardDetailModal;
