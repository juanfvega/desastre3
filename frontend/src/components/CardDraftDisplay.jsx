// src/components/CardDraftDisplay.jsx

import React from 'react';
import Card from './Card'; // Asegúrate de que esta ruta sea correcta para tu Card.jsx
import './CardDraftDisplay.css'; // Opcional: para darle estilo a la mesa de draft

const CardDraftDisplay = ({ draftCards, onCardSelect }) => {
    // Si no hay cartas, mostrar el mensaje (el cual deberías tener en tu CardDraftDisplay)
    if (!draftCards || draftCards.length === 0) {
        return (
            <div className="card-draft-container">
                <p>Esperando a la preparación del mazo...</p>
            </div>
        );
    }

    return (
        <div className="card-draft-container">
            <div className="draft-cards-list">
                {draftCards.map((card, index) => (
                
                    <div 
                        key={index} 
                        className="draft-card-item"
                        onClick={() => onCardSelect(card)} 
                    >
                        <Card 
                            card={card} 
                        />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CardDraftDisplay;