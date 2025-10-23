// WebSocketContext.jsx
import React, { createContext, useContext, useEffect, useRef } from 'react';
import { createWSService } from '../../services/wsService';


// Creamos un WebSocketContext que provea la conexión a todos los componentes:
const WebSocketContext = createContext(null);


export const WebSocketProvider = ({ children }) => {
// useRef mantiene la misma instancia de WebSocket durante toda la vida del Provider
// Todos los componentes hijos pueden acceder a ws.current usando el hook useWebSocket()
  const ws = useRef(null);

  const init = () => {
    // llamamos al service ws
    ws.current = createWSService();
    //ws.current.connect();
    
  };

  useEffect(() => {
    // init(); // inicialización
    // return () => ws.current?.disconnect();
  }, []);

  return <WebSocketContext.Provider value={ws.current}>{children}</WebSocketContext.Provider>;
};

export const useWebSocket = () => useContext(WebSocketContext);
