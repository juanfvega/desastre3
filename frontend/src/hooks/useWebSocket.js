import { useEffect, useRef, useState, useCallback } from 'react';

const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [secretCards, setSecretCards] = useState([]);
  const [currentPlayer, setCurrentPlayer] = useState(null);
  const [isActivePlayer, setIsActivePlayer] = useState(false);
  const [turnState, setTurnState] = useState({
    canExecuteAction: false,
    mustDiscard: false,
    canEndTurn: false,
    actionExecuted: false
  });
  const [playerId, setPlayerId] = useState(null); // ID del jugador actual
  const [Cards, setCards] = useState([]);
  const [error, setError] = useState(null);
  const websocketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket conectado');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Mensaje recibido del WebSocket:', data);

          // Escuchar específicamente el evento "player_secrets_assigned"
          if (data.event === 'player_secrets_assigned') {
            console.log('Evento player_secrets_assigned recibido:', data);
            
            // Actualizar las cartas secretas con los datos recibidos
            if (data.secrets && Array.isArray(data.secrets)) {
              setSecretCards(data.secrets);
              console.log('Cartas secretas actualizadas:', data.secrets);
            } else if (data.payload && data.payload.secrets && Array.isArray(data.payload.secrets)) {
              // Manejar estructura alternativa del payload
              setSecretCards(data.payload.secrets);
              console.log('Cartas secretas actualizadas (payload):', data.payload.secrets);
            } else {
              console.warn('Formato de datos inesperado para player_secrets_assigned:', data);
            }
          }

          // Escuchar evento de cambio de turno (broadcast a todos los jugadores)
          if (data.event === 'turn_changed' || data.event === 'current_turn' || data.event === 'turn_info') {
            console.log('Evento de turno recibido:', data);
            
            // Actualizar información del jugador actual
            if (data.current_player) {
              setCurrentPlayer(data.current_player);
              console.log('Jugador actual actualizado:', data.current_player);
            } else if (data.payload && data.payload.current_player) {
              // Manejar estructura alternativa del payload
              setCurrentPlayer(data.payload.current_player);
              console.log('Jugador actual actualizado (payload):', data.payload.current_player);
            } else if (data.player) {
              // Otra posible estructura
              setCurrentPlayer(data.player);
              console.log('Jugador actual actualizado (player):', data.player);
            } else {
              console.warn('Formato de datos inesperado para evento de turno:', data);
            }

            // Determinar si este jugador es el activo
            if (playerId && data.current_player && data.current_player.id === playerId) {
              setIsActivePlayer(true);
              setTurnState({
                canExecuteAction: true,
                mustDiscard: false,
                canEndTurn: false,
                actionExecuted: false
              });
            } else {
              setIsActivePlayer(false);
            }
          }

          // Escuchar eventos de actualización de turno (turn.update)
          if (data.event === 'turn.update' || data.event === 'turn_update') {
            console.log('Evento turn.update recibido:', data);
            
            // Actualizar estado del turno
            if (data.turn_state || data.payload) {
              const turnData = data.turn_state || data.payload;
              setTurnState(prevState => ({
                ...prevState,
                canExecuteAction: turnData.canExecuteAction !== undefined ? turnData.canExecuteAction : prevState.canExecuteAction,
                mustDiscard: turnData.mustDiscard !== undefined ? turnData.mustDiscard : prevState.mustDiscard,
                canEndTurn: turnData.canEndTurn !== undefined ? turnData.canEndTurn : prevState.canEndTurn,
                actionExecuted: turnData.actionExecuted !== undefined ? turnData.actionExecuted : prevState.actionExecuted
              }));
              console.log('Estado del turno actualizado:', turnData);
            }
          }

          // Escuchar evento de identificación del jugador
          if (data.event === 'player_id' || data.event === 'player_identified') {
            console.log('ID del jugador recibido:', data);
            if (data.player_id || data.id) {
              setPlayerId(data.player_id || data.id);
            }
          }
        } catch (error) {
          console.error('Error al parsear mensaje del WebSocket:', error);
        }

        try {
          const data = JSON.parse(event.data);
          if (data.event === 'player_cards_assigned') {
            if (data.cards && Array.isArray(data.cards)) {
              setCards(data.cards);
            }
          }
        } catch (error) {
          console.error('Error al parsear mensaje del WebSocket:', error);
        }
      }

      ws.onclose = (event) => {
        console.log('WebSocket desconectado:', event.code, event.reason);
        setIsConnected(false);
        websocketRef.current = null;

        // Intentar reconexión automática si no fue un cierre intencional
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttempts.current) * 1000; // Backoff exponencial
          console.log(`Intentando reconexión en ${timeout}ms (intento ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, timeout);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError('No se pudo reconectar al servidor después de varios intentos');
        }
      };

      ws.onerror = (error) => {
        console.error('Error en WebSocket:', error);
        setError('Error de conexión WebSocket');
      };

    } catch (error) {
      console.error('Error al crear conexión WebSocket:', error);
      setError('Error al conectar con el servidor');
    }
  }, [url]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Desconexión intencional');
      websocketRef.current = null;
    }
    
    setIsConnected(false);
    reconnectAttempts.current = 0;
  }, []);

  const sendMessage = useCallback((message) => {
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      try {
        const messageToSend = typeof message === 'string' ? message : JSON.stringify(message);
        websocketRef.current.send(messageToSend);
        console.log('Mensaje enviado:', messageToSend);
      } catch (error) {
        console.error('Error al enviar mensaje:', error);
        setError('Error al enviar mensaje');
      }
    } else {
      console.warn('WebSocket no está conectado. No se puede enviar el mensaje:', message);
      setError('WebSocket no está conectado');
    }
  }, []);

  // Efecto para establecer la conexión inicial
  useEffect(() => {
    if (url) {
      connect();
    }

    // Cleanup al desmontar el componente
    return () => {
      disconnect();
    };
  }, [url, connect, disconnect]);

  return {
    isConnected,
    secretCards,
    currentPlayer,
    isActivePlayer,
    turnState,
    playerId,
    Cards,
    error,
    sendMessage,
    connect,
    disconnect
  };
};

export default useWebSocket;
