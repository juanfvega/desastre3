import './TurnInfo.css';

const TurnInfo = ({ currentPlayer, isConnected = false, turnState = null }) => {
  // Si no hay jugador actual, mostrar estado de carga o mensaje apropiado
  if (!currentPlayer) {
    return (
      <div className="turn-info turn-info-loading">
        <div className="turn-info-content">
          <div className="turn-avatar turn-avatar-loading">
            <div className="default-avatar">?</div>
          </div>
          <div className="turn-player-name">
            {isConnected ? 'Esperando turno...' : 'Sin conexión'}
          </div>
        </div>
        <div className="turn-label">
          {isConnected ? 'Cargando información' : 'Modo sin conexión'}
        </div>
      </div>
    );
  }

  // Determinar el estado visual del turno
  const getTurnStatus = () => {
    if (turnState?.lastAction === "skip_action") {
      return {
        label: 'Turno omitido',
        className: 'turn-skipped'
      };
    }
    if (turnState?.actionExecuted === false && turnState?.canExecuteAction === false) {
      return {
        label: 'Sin acción ejecutada',
        className: 'turn-no-action'
      };
    }
    if (turnState?.mustDiscard) {
      return {
        label: 'Debe descartar',
        className: 'turn-must-discard'
      };
    }
    if (turnState?.canEndTurn) {
      return {
        label: 'Puede terminar turno',
        className: 'turn-can-end'
      };
    }
    return {
      label: 'Turno actual',
      className: ''
    };
  };

  const status = getTurnStatus();

  return (
    <div className={`turn-info ${status.className}`}>
      <div className="turn-info-content">
        <div className="turn-avatar">
          {currentPlayer.avatar ? (
            <img src={currentPlayer.avatar} alt={`Avatar de ${currentPlayer.name}`} />
          ) : (
            <div className="default-avatar">
              {currentPlayer.name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <div className="turn-player-name">
          {currentPlayer.name}
        </div>
      </div>
      <div className="turn-label">
        {status.label}
      </div>
    </div>
  );
};

export default TurnInfo;