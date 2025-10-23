import './SecretCard.css';

const SecretCard = ({ card }) => {
  return (
    <div className="secret-card">
      <div className="secret-card-header">
        <h3 className="secret-card-title">{card.name}</h3>
        <div className="secret-card-type">{card.type}</div>
      </div>
      
      <div className="secret-card-content">
        <div className="secret-card-image">
          {card.image ? (
            <img src={card.image} alt={card.name} />
          ) : (
            <div className="placeholder-image">
              <span>🃏</span>
            </div>
          )}
        </div>
        
        <div className="secret-card-description">
          <p>{card.description}</p>
        </div>
        
        {card.points && (
          <div className="secret-card-points">
            <span className="points-label">Puntos:</span>
            <span className="points-value">{card.points}</span>
          </div>
        )}
        
        {card.condition && (
          <div className="secret-card-condition">
            <span className="condition-label">Condición:</span>
            <p className="condition-text">{card.condition}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SecretCard;