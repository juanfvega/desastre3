import { useState } from 'react';
import CardModal from '../../components/CardModal';
import '../../App.css';

/**
 * DisplayCards unificado:
 * - Base de mergep0 (gameId, playerId, onHandRefresh)
 * - Compat con dev (onClickLookIntoAshes, setCards, gameData, player)
 */
function DisplayCards({
  // mergep0
  cards = [],
  onDiscardAction,
  gameId,
  playerId,
  onHandRefresh,

  // dev (compat)
  onClickLookIntoAshes,
  selectedDiscardPileCard,
  setCards,
  gameData,
  player,
}) {
  const [isCardModalOpen, setIsCardModalOpen] = useState(false);

  // Usar únicamente las cartas recibidas por props
  const displayCards = Array.isArray(cards) ? cards : [];
  const cardCount = displayCards.length;

  const getButtonImage = () => {
    const imageId = cardCount >= 0 && cardCount <= 6 ? cardCount : 0;
    return `${import.meta.env.BASE_URL}buttons/card_back_${imageId}.png`;
  };

  const handleOpenCardModal = () => setIsCardModalOpen(true);
  const handleCloseCardModal = () => setIsCardModalOpen(false);

  return (
    <>
      <div className="card">
        <div
          onClick={handleOpenCardModal}
          style={{ cursor: 'pointer', display: 'inline-block' }}
        >
          <img
            src={getButtonImage()}
            style={{ width: '150px', height: 'auto', transition: 'all 0.3s ease', marginLeft: '-150px' }}
            alt="Ver mis cartas"
          />
        </div>
      </div>

      {/* Modal de Cartas */}
      <CardModal
        isOpen={isCardModalOpen}
        onClose={handleCloseCardModal}
        Cards={displayCards}
        onDiscardAction={onDiscardAction}
        // mergep0
        gameId={gameId}
        playerId={playerId}
        onHandRefresh={onHandRefresh}
        // dev (compat)
        onClickLookIntoAshes={onClickLookIntoAshes}
        selectedDiscardPileCard={selectedDiscardPileCard}
        setCards={setCards}
        gameData={gameData}
        player={player}
      />
    </>
  );
}

export default DisplayCards;
