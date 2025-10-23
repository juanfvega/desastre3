import React, { useEffect, useState } from "react";
import DiscardPile from "../../components/DiscardPile";


const ViewRegularAndDiscardDecks = ({ deckInfo }) => {
  const [regularDeckCount, setRegularDeckCount] = useState(0);
  const [discardPile, setDiscardPile] = useState([]);
  
  // useEffect para actualizar estados cuando deckInfo cambia
  useEffect(() => {
    if(deckInfo){
      setRegularDeckCount(deckInfo.countMazo ?? 0);
      setDiscardPile(Array.isArray(deckInfo.descarteVisible) ? deckInfo.descarteVisible : []);
    }
  }, [deckInfo]);



  return (
    <div className="view-decks-container">
      <div className="decks-section">
        {/* Mazo Regular */}
        <div className="deck-box">
            <p className="deck-title" data-testid="regular-deck">  Mazo regular : {regularDeckCount} 🂠</p>
          <div className="deck-back" />
        </div>

        {/* Mazo de Descarte */}
        <div className="deck-box">
          <p className="deck-title" data-testid="discard-pile">Mazo de descarte</p>
          {discardPile.length > 0 ? (
            <DiscardPile cards={discardPile} />
          ) : (
            <p>No hay cartas en el mazo de descarte</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ViewRegularAndDiscardDecks;