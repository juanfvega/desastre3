import "./secrets.css";
import React, { useState } from "react";
import SecretsModal from "../../components/SecretsModal";
import TurnInfo from "../../components/TurnInfo";
import GameScreen from "../../components/GameScreen";
import ActionButton from "../../components/ActionButton";

// ⬇️ importamos helpers modularizados
import { setPlayersCount, seatCardStyle } from "./tableLayout";

// 👇 Importamos el array exportado del lobby (fallback si no existe)
let lobbyPlayers = [];
try {
  const lobbyModule = require("./CreateLobby");
  lobbyPlayers = lobbyModule.lobbyPlayers || [];
} catch {
  // Fallback players for testing
  lobbyPlayers = [
    { id: 1, name: "Jugador Test 1" },
    { id: 2, name: "Jugador Test 2" },
    { id: 3, name: "Jugador Test 3" },
    { id: 4, name: "Jugador Test 4" }
  ];
}

const SECRETS = [
  { id: "001", title: "Secreto #1", img: "/secrets/001.png", x: 0, y: 600 },
  { id: "002", title: "Secreto #2", img: "/secrets/002.png", x: 300, y: 600 },
  { id: "003", title: "Secreto #3", img: "/secrets/003.png", x: 600, y: 600 },
];

export default function InGameTest() {
  const [isSecretsModalOpen, setIsSecretsModalOpen] = useState(false);
  const [testScenario, setTestScenario] = useState(0);
  const [actionLog, setActionLog] = useState([]);

  // Datos de test para diferentes escenarios
  const testScenarios = [
    {
      name: "Scenario 1: Cartas Básicas",
      mockSecretCards: [
        {
          id: 1,
          name: "La Cosa",
          type: "Infección",
          description: "Eres La Cosa. Tu objetivo es infectar a todos los demás jugadores.",
          condition: "Ganar eliminando a todos los humanos",
          image: "/secrets/la-cosa.jpg"
        },
        {
          id: 2,
          name: "Lanzallamas",
          type: "Acción",
          description: "Elimina a un jugador adyacente. Esta carta es muy poderosa.",
          condition: "Solo se puede usar una vez por partida",
          image: "/secrets/lanzallamas.jpg"
        },
        {
          id: 3,
          name: "Determinación",
          type: "Defensa",
          description: "No puedes ser eliminado en este turno. Te protege de ataques.",
          condition: "Se descarta después de usar",
          image: "/secrets/determinacion.jpg"
        }
      ],
      mockCurrentPlayer: { id: 1, name: "Jugador Test", avatar: null },
      isActivePlayer: false,
      isConnected: true,
      turnState: { canExecuteAction: false, actionExecuted: false, state: "waiting" }
    },
    {
      name: "Scenario 2: Jugador Activo",
      mockSecretCards: [
        {
          id: 4,
          name: "Vigía",
          type: "Acción",
          description: "Mira las cartas secretas de un jugador adyacente sin que se entere.",
          condition: "Solo una vez por turno"
        },
        {
          id: 5,
          name: "Whisky",
          type: "Pánico",
          description: "Intercambia tu mano completa con la de otro jugador.",
          condition: "Solo si tienes 4 o más cartas"
        }
      ],
      mockCurrentPlayer: { id: 1, name: "Tu Jugador", avatar: "/avatar/player1.jpg" },
      isActivePlayer: true,
      isConnected: true,
      turnState: { canExecuteAction: true, actionExecuted: false, state: "can-end" }
    },
    {
      name: "Scenario 3: Muchas Cartas",
      mockSecretCards: [
        { id: 6, name: "Sospecha", type: "Pánico", description: "Fuerza a un jugador a revelar una carta aleatoria.", condition: "Solo durante el día" },
        { id: 7, name: "Cuarentena", type: "Obstáculo", description: "Un jugador no puede intercambiar cartas.", condition: "Dura hasta el final del turno" },
        { id: 8, name: "Análisis", type: "Acción", description: "Revela si un jugador está infectado.", condition: "No se puede usar de noche" },
        { id: 9, name: "Hacha", type: "Acción", description: "Elimina a un jugador.", condition: "Solo si estás infectado" },
        { id: 10, name: "Seducción", type: "Pánico", description: "Intercambia una carta con un jugador adyacente.", condition: "Solo de noche" },
        { id: 11, name: "Cadenas", type: "Obstáculo", description: "Un jugador no puede jugar cartas de Acción.", condition: "Dura 2 turnos" }
      ],
      mockCurrentPlayer: { id: 2, name: "Otro Jugador", avatar: null },
      isActivePlayer: false,
      isConnected: false,
      turnState: { canExecuteAction: false, actionExecuted: true, state: "no-action" }
    }
  ];

  const currentScenario = testScenarios[testScenario];

  const addToLog = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setActionLog(prev => [...prev, `[${timestamp}] ${message}`]);
  };

  const handleOpenSecretsModal = () => {
    setIsSecretsModalOpen(true);
    addToLog(`🔍 Modal de secretos abierto - Mostrando ${currentScenario.mockSecretCards.length} cartas`);
  };

  const handleCloseSecretsModal = () => {
    setIsSecretsModalOpen(false);
    addToLog("❌ Modal de secretos cerrado");
  };

  const handleNoAction = () => {
    addToLog(`⚡ Jugador ${currentScenario.mockCurrentPlayer.name} ejecutó "No Action"`);
  };

  const nextScenario = () => {
    const nextIndex = (testScenario + 1) % testScenarios.length;
    setTestScenario(nextIndex);
    addToLog(`🔄 Cambiando a: ${testScenarios[nextIndex].name}`);
  };

  const clearLog = () => {
    setActionLog([]);
  };

  // 👉 seteamos la cantidad (no cambia ningún parámetro de seatCardStyle)
  setPlayersCount(lobbyPlayers.length);

  return (
    <GameScreen>
      {/* Panel de Control de Test */}
      <div style={{
        position: 'fixed',
        top: '10px',
        left: '10px',
        right: '10px',
        zIndex: 999999,
        background: 'rgba(0, 0, 0, 0.9)',
        padding: '15px',
        borderRadius: '8px',
        border: '2px solid #4CAF50',
        maxHeight: '180px',
        overflow: 'auto'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '10px',
          flexWrap: 'wrap',
          gap: '10px'
        }}>
          <h3 style={{ 
            color: '#4CAF50', 
            margin: 0,
            fontSize: 'clamp(1rem, 3vw, 1.2rem)'
          }}>
            🧪 TEST SECRETOS - {currentScenario.name}
          </h3>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button 
              onClick={nextScenario}
              style={{
                padding: '8px 12px',
                background: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Siguiente ({testScenario + 1}/{testScenarios.length})
            </button>
            <button 
              onClick={clearLog}
              style={{
                padding: '8px 12px',
                background: '#FF9800',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Limpiar Log
            </button>
          </div>
        </div>
        
        <div style={{ 
          maxHeight: '60px', 
          overflow: 'auto',
          background: 'rgba(255, 255, 255, 0.1)',
          padding: '8px',
          borderRadius: '4px',
          fontSize: 'clamp(0.7rem, 1.8vw, 0.8rem)'
        }}>
          {actionLog.length === 0 ? (
            <p style={{ color: '#999', margin: 0, fontStyle: 'italic' }}>
              Log de acciones aparecerá aquí...
            </p>
          ) : (
            actionLog.slice(-3).map((log, index) => (
              <p key={index} style={{ color: '#FFF', margin: '2px 0', lineHeight: '1.2' }}>
                {log}
              </p>
            ))
          )}
        </div>
      </div>

      <div className="se-app">
        {/* Imagen de la mesa */}
        <div className="se-table">
          <img className="se-table" src="/secrets/wood.jpg" alt="Mesa de secretos" />
        </div>

        {/* 3 cartas por jugador, EXCEPTO el de abajo (seatIndex === 2) */}
        {lobbyPlayers.map((player, seatIndex) =>
          seatIndex === 2
            ? null // el de abajo sin cartas, como antes
            : [0, 1, 2].map((cIdx) => {
                const secret = SECRETS[cIdx % SECRETS.length];
                const pos = seatCardStyle(seatIndex, cIdx);
                return (
                  <div
                    key={`${player.id}-${seatIndex}-${cIdx}`}
                    className="se-card seat-card"
                    style={{ position: "absolute", zIndex: 5, ...pos }}
                  >
                    <img className="se-thumb" src={secret.img} alt={secret.title} />
                    <h2 className="se-title">
                      {player.name} - {secret.title}
                    </h2>
                  </div>
                );
              })
        )}

        {/* Renderizar nombres de jugadores */}
        <div className="players-overlay">
          {lobbyPlayers?.map((p, i) => (
            <div
              key={p.id ?? i}
              className="player-chip"
              style={{
                position: "absolute",
                ...(i === 0 && { top: 20, left: "50%", transform: "translateX(-50%)" }),
                ...(i === 1 && { top: "50%", right: 20, transform: "translateY(-50%)" }),
                ...(i === 2 && { bottom: 20, left: "50%", transform: "translateX(-50%)" }),
                ...(i === 3 && { top: "50%", left: 20, transform: "translateY(-50%)" }),
                ...(i === 4 && { top: 120, left: "20%" }),
                ...(i === 5 && { top: 120, right: "20%" }),
              }}
            >
              {p.name}
            </div>
          ))}
        </div>
      </div>
      
      {/* Información del turno actual */}
      <TurnInfo 
        currentPlayer={currentScenario.mockCurrentPlayer} 
        isConnected={currentScenario.isConnected} 
        turnState={currentScenario.turnState}
      />
      
      {/* Botón de acción "No ejecutar acción" */}
      <ActionButton
        onNoAction={handleNoAction}
        isVisible={currentScenario.isActivePlayer && currentScenario.turnState.canExecuteAction && !currentScenario.turnState.actionExecuted}
        disabled={!currentScenario.isConnected}
      />
      
      {/* Botón para ver secretos - COMPONENTE PRINCIPAL A PROBAR */}
      <div className="secrets-button-container">
        <button 
          onClick={handleOpenSecretsModal}
          className="secrets-button"
          style={{
            background: 'linear-gradient(145deg, #8B4513, #A0522D)',
            color: '#FBE9B9',
            border: '2px solid #D2691E',
            padding: '12px 20px',
            borderRadius: '8px',
            fontFamily: 'Georgia, serif',
            fontWeight: 'bold',
            fontSize: 'clamp(0.9rem, 2.5vw, 1.1rem)',
            cursor: 'pointer',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
            transition: 'all 0.3s ease',
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            zIndex: 1000
          }}
        >
          🔍 Ver mis secretos ({currentScenario.mockSecretCards.length})
        </button>
      </div>

      {/* Información de test en el centro */}
      <div style={{ 
        padding: '200px 15px 80px', 
        textAlign: 'center',
        color: 'rgba(251, 233, 185, 0.9)',
        fontFamily: 'Georgia, serif',
        position: 'relative',
        zIndex: 50
      }}>
        <h2 style={{ 
          fontSize: 'clamp(1.5rem, 4vw, 2.5rem)',
          margin: '0 0 20px 0'
        }}>🎮 Test de "Ver Mis Secretos"</h2>
        
        <div style={{ 
          background: 'rgba(19, 15, 11, 0.9)', 
          padding: '20px', 
          borderRadius: '8px',
          maxWidth: '500px',
          margin: '0 auto',
          border: '1px solid rgba(251, 233, 185, 0.3)'
        }}>
          <h3 style={{ color: '#4CAF50', marginTop: 0 }}>🧪 Estado del Test Actual</h3>
          <p><strong>Escenario:</strong> {currentScenario.name}</p>
          <p><strong>Cartas disponibles:</strong> {currentScenario.mockSecretCards.length}</p>
          <p><strong>Jugador activo:</strong> {currentScenario.isActivePlayer ? '✅ Sí' : '❌ No'}</p>
          <p><strong>Conexión:</strong> 
            <span style={{ color: currentScenario.isConnected ? '#4CAF50' : '#f44336' }}>
              {currentScenario.isConnected ? ' ✅ Conectado' : ' ❌ Desconectado'}
            </span>
          </p>
          
          <div style={{ 
            marginTop: '15px', 
            padding: '10px', 
            background: 'rgba(33, 150, 243, 0.2)', 
            borderRadius: '4px',
            border: '1px solid rgba(33, 150, 243, 0.3)'
          }}>
            <h4 style={{ color: '#2196F3', margin: '0 0 8px 0' }}>📋 Instrucciones de Prueba:</h4>
            <ul style={{ textAlign: 'left', fontSize: '0.9rem', margin: 0, paddingLeft: '20px' }}>
              <li>Haz clic en "🔍 Ver mis secretos" (esquina inferior derecha)</li>
              <li>Verifica que se abra el modal correctamente</li>
              <li>Revisa que se muestren las cartas del escenario actual</li>
              <li>Prueba cerrar con X y haciendo clic fuera del modal</li>
              <li>Cambia de escenario para probar con diferentes cantidades de cartas</li>
              <li>Observa el log de acciones para ver el comportamiento</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 🎯 COMPONENTE PRINCIPAL A PROBAR: Modal de Cartas Secretas */}
      <SecretsModal
        isOpen={isSecretsModalOpen}
        onClose={handleCloseSecretsModal}
        secretCards={currentScenario.mockSecretCards}
      />
    </GameScreen>
  );
}