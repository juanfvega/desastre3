import React from 'react';
import './CardDraftDetail.css'; // You'll create this CSS file

const CardDraftDetail = ({ isOpen, onClose, card,  onDraftAction }) => {
    if (!isOpen || !card) return null;

    const imageId =  card.name;
    const imagePath = `/Cards/${imageId}.png`; 
    if (!imageId) return null; 

    return (
        <div className="card-detail-overlay" onClick={onClose}>
            <div className="card-detail-content" onClick={(e) => e.stopPropagation()}>
                
                {/* 1. Imagen de la Carta Agrandada */}
                <div className="card-detail-image-wrapper">
                    <img 
                        src={imagePath} 
                        alt={`Carta ${imageId}`} 
                        className="card-detail-image" 
                    />
                </div>

                <div className="card-detail-buttons">
                    <button onClick={() => onDraftAction(card)} className="detail-button Draft">
                        Agarrar
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CardDraftDetail;