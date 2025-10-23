import { useEffect } from 'react';
import SecretCard from './SecretCard';
import './SecretsModal.css';

const SecretsModal = ({ isOpen, onClose, secretCards }) => {
  // Close modal on Escape key press
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent background scrolling when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="secrets-modal-overlay" onClick={onClose}>
      <div className="secrets-modal" onClick={(e) => e.stopPropagation()}>
        <div className="secrets-modal-header">
          <h2 className="secrets-modal-title">Mis Cartas Secretas</h2>
          <button 
            className="secrets-modal-close" 
            onClick={onClose}
            aria-label="Cerrar modal"
          >
            ×
          </button>
        </div>
        
        <div className="secrets-modal-content">
          {secretCards && secretCards.length > 0 ? (
            <div className="secret-cards-grid">
              {secretCards.map((card, index) => (
                <SecretCard key={card.id || index} card={card} />
              ))}
            </div>
          ) : (
            <div className="no-secrets-message">
              <p>No tienes cartas secretas asignadas.</p>
            </div>
          )}
        </div>
        
        <div className="secrets-modal-footer">
          <button className="close-button" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default SecretsModal;