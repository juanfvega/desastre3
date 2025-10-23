import React from 'react';

import './Card.css';

const CARD_TYPE_COLORS = {
    'detective': 'border-blue', 
    'devious': 'border-purple',     
    'event': 'border-green', 
    'instant': 'border-green-oil' 
};

const Card = ({ card, onCardClick , className}) => {
  if (!card || !card.name) {
    return null; // Manejo de caso donde card o card.name no están definidos
  }
  const imagePath = `/Cards/${card.name}.png`;

  // 1. Extraer el tipo del nombre (la parte antes del primer '_')
  const getCardType = (name) => {
    const type = name.split('_')[0]; 
    return CARD_TYPE_COLORS[type] || 'border-default'; 
  };

  // 2. Obtener la clase de borde dinámicamente
  const borderClass = getCardType(card.name);

  return (
    <div
      className={`card-image-container ${borderClass} ${className || ''}`}
      onClick={() => onCardClick(card)}
      style={{ cursor: 'pointer' }}
    >
      <img src={imagePath} alt={`Carta ${card.name}`} className={`card-image-png ${className || ''}`} />
    </div>
  );
};

export default Card;