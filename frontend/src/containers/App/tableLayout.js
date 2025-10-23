// Compatibilidad para tests + nuevo layout circular
// Asegurate de dejar este archivo EXACTAMENTE en: /src/containers/App/tableLayout.js

const CENTER_X = 50;  // centro horizontal (%)
const CENTER_Y = 50;  // centro vertical (%)
const RADIUS   = 35;  // radio del círculo (%)

let PLAYERS_COUNT = 2; // usado por tests antiguos
export const setPlayersCount = (n) => {
  PLAYERS_COUNT = Math.max(2, Math.min(6, n || 2));
};

/** ---- Nuevo: posiciones en círculo para N rivales (0..5) ---- */
export function getSeatPositions(count) {
  const angleSets = {
    1: [90],                      // arriba
    2: [45, 135],                 // arriba-der / arriba-izq
    3: [0, 90, 180],              // der / arriba / izq
    4: [20, 90, 160, 200],        // der-sup / sup / izq-sup / izq-inf
    5: [350, 35, 90, 145, 200],   // repartidos más fino
  };
  const clamped = Math.max(0, Math.min(5, count || 0));
  const angles = angleSets[clamped] || [];

  return angles.map((deg) => {
    const rad = (deg * Math.PI) / 180;
    const x = CENTER_X + RADIUS * Math.cos(rad);  // left
    const y = CENTER_Y - RADIUS * Math.sin(rad);  // top
    return {
      top:  `${y}%`,
      left: `${x}%`,
      transform: "translate(-50%, -50%)",
    };
  });
}

/** ---- Nuevo: excluir jugador actual ---- */
export function getOtherPlayers(listPlayers = [], myId) {
  return listPlayers.filter((p) => p.id !== myId);
}

/** ============================================================
 *  Compat con API vieja que usan tus tests:
 *  - seatCardStyle(seatIndex, cardIndex)
 *  - seatPlayerNameStyle(seatIndex)
 *  Estas funciones se basan en getSeatPositions para no romper tests.
 *  ============================================================ */
export const seatCardStyle = (seatIndex, cardIndex = 1) => {
  // Para compat: usamos PLAYERS_COUNT-1 asumiendo 1 es “yo” y el resto rivales
  const seats = getSeatPositions(Math.min(5, Math.max(0, PLAYERS_COUNT - 1)));
  const pos = seats[(seatIndex % (seats.length || 1))] || {
    top: "50%", left: "50%", transform: "translate(-50%, -50%)"
  };

  const spread = 80; // px entre cartas para que los tests vean desplazamiento
  return {
    top: pos.top,
    left: `calc(${pos.left} + ${(cardIndex - 1) * spread}px)`,
    transform: pos.transform,
  };
};

export const seatPlayerNameStyle = (seatIndex) => {
  const seats = getSeatPositions(Math.min(5, Math.max(0, PLAYERS_COUNT - 1)));
  const pos = seats[(seatIndex % (seats.length || 1))] || {
    top: "50%", left: "50%", transform: "translate(-50%, -50%)"
  };
  return {
    top: pos.top,
    left: pos.left,
    transform: pos.transform,
  };
};
