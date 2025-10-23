import React, { useState, useEffect } from 'react';
import { createHttpService } from '../../services/HttpService';
import './SetsModal.css';
import SetCard from '../../components/SetCard';


// Componente para mostrar un set individual
const SetDisplay = ({ set }) => (
    set.cards.map((card, idx) => (
            <div key={idx}>
                <SetCard key={idx} card={card} className="sets-thumbnail" />
            </div>
    )));

// Componente principal modal
const SetsModal = ({ isOpen, onClose, gameId, playerId }) => {
    const httpService = createHttpService();
  
    // Mock de setsByPlayer para testeo con nombres reales de detectives y eventos (sin detectiveType)
  const mockSetsByPlayer = {
    'Jugador1': [
      {
        cards: [
          { name: 'detective_quin' },
          { name: 'detective_quin' },
        ]
      },
      {
        cards: [
          { name: 'detective_poirot' },
          { name: 'detective_poirot' },
          { name: 'detective_poirot' }
        ]
      }
    ],
    'Jugador2': [
      {
        cards: [
            { name: 'detective_marple' },
            { name: 'detective_marple' },
            { name: 'detective_marple' },
        ]
      },
      {
        cards: [
          { name :'detective_oliver' },
          { name :'detective_oliver' },
          { name :'detective_oliver' },
        ]
      }
    ]
  };

  // Para testear el renderizado, reemplaza el estado setsByPlayer por el mock
  const [setsByPlayer, setSetsByPlayer] = useState(mockSetsByPlayer);
  // WebSocket code aquí si lo necesitas

  useEffect(() => {
    if (isOpen) {
      httpService.watchSets(gameId).then(data => {
        console.log("watchSets GET sets data:", data);
        setSetsByPlayer(data); // Suponiendo que data es { jugadorA: [sets], jugadorB: [sets] }
      });
      // Suscribirse a WebSocket aquí
      // ...
    }
  }, [isOpen, gameId]);

  if (!isOpen) return null;

  return (
    <>
    <button onClick={onClose} className="close-button">Cerrar</button>
    <div className="sets-modal-overlay" onClick={onClose}>
      <div className="sets-modal" onClick={e => e.stopPropagation()}>
        <h2>Sets jugados</h2>
        <div className="sets-players-container">
          {Object.entries(setsByPlayer).map(([player, sets]) => (
            <div
              key={player}
              className={`player-sets-group ${player === playerId ? 'current-player' : ''}`}
            >
              <div className="player-name">{player}</div>
              <div className="sets-list">
                {sets.map((set, idx) => (
                  <div key={idx} className="set-group">
                    <SetDisplay set={set} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
    </>
  );
};

export default SetsModal;