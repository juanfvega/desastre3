// services/wsService.js
const WS_BASE = import.meta.env?.VITE_WS_BASE ?? "ws://127.0.0.1:8000";

export const createWSService = () => {
  let ws = null;
  let connected = false;

  let lastGameId = null;
  // let lastPlayerId = null;
  let lastUrl = null;

  // Reintentos automáticos
  let shouldReconnect = true;
  let attempts = 0;
  const MAX_ATTEMPTS = 5;
  const BASE_DELAY = 1000;
  const MAX_DELAY = 5000;

  // Listeners
  const listeners = new Map(); // Map<string, Set<fn>>

  // Construye la ruta esperada por el backend
  const buildUrl = (gameId) => `${WS_BASE}/ws/games/${gameId}`;

  // --- Gestión de listeners ---
  const addListener = (event, cb) => {
    if (!listeners.has(event)) listeners.set(event, new Set());
    listeners.get(event).add(cb);
  };

  const removeListener = (event, cb) => {
    if (listeners.has(event)) listeners.get(event).delete(cb);
  };

  const emit = (event, payload) => {
    const set = listeners.get(event);
    if (!set) return;
    for (const cb of Array.from(set)) {
      try {
        cb(payload);
      } catch (e) {
        console.error("[WS] listener error:", e);
      }
    }
  };

  // --- Parser de mensajes entrantes ---
  const safeParseAndEmit = (evt) => {
    try {
      const raw = evt?.data;
      if (!raw) return;

      let msg;
      try {
        msg = typeof raw === "string" ? JSON.parse(raw) : raw;
      } catch {
        // Si no es JSON válido, se ignora
        console.warn("[WS] mensaje no JSON:", raw);
        return;
      }

      // Soporta múltiples formatos
      // { event: "cards_dealt", data: {...} }
      // { type: "game.turn.changed", payload: {...} }
      const type = msg.type ?? msg.event;
      if (!type) return;

      const payload = msg.payload ?? msg.data ?? msg;
      // DEBUG: log global de todos los eventos recibidos
      emit(type, payload);
    } catch (err) {
      console.error("[WS] Error parsing message:", err);
    }
  };

  // --- Reintento con backoff exponencial suave ---
  const scheduleReconnect = () => {
    if (!shouldReconnect) return;
    if (attempts >= MAX_ATTEMPTS) {
      console.warn("[WS] reconnection max attempts reached");
      return;
    }
    attempts += 1;
    const delay = Math.min(BASE_DELAY * attempts, MAX_DELAY);
    console.log(`[WS] reconnect attempt ${attempts} in ${delay}ms`);
    setTimeout(() => {
      if (lastGameId) {
        connect(lastGameId);
      } else if (lastUrl) {
        connectByUrl(lastUrl);
      }
    }, delay);
  };

  // --- Configura eventos básicos del socket ---
  const bindSocket = () => {
    if (!ws) return;

    ws.onopen = () => {
      connected = true;
      attempts = 0;
      console.log("[WS] connected:", lastUrl);
    };

    ws.onmessage = safeParseAndEmit;

    ws.onclose = (e) => {
      connected = false;
      ws = null;
      console.warn("[WS] disconnected:", e?.code ?? "");
      scheduleReconnect();
    };

    ws.onerror = (err) => {
      console.error("[WS] error:", err);
      // onclose se encargará de reconectar
    };
  };

  // --- Conexión estándar por gameId ---
  const connect = (gameId) => {
    if (!gameId) {
      console.error("[WS] connect(): falta gameId", { gameId });
      return;
    }
    shouldReconnect = true;
    lastGameId = gameId;
    lastUrl = buildUrl(gameId);

    try {
      console.log("[WS] connecting to:", lastUrl);
      ws = new WebSocket(lastUrl);
      bindSocket();
    } catch (error) {
      connected = false;
      console.error("[WS] connect failed:", error);
      scheduleReconnect();
    }
  };

  // --- Conexión directa por URL (usada por InGame.jsx) ---
  const connectByUrl = (url) => {
    shouldReconnect = true;
    lastUrl = url?.startsWith("ws") ? url : `${WS_BASE}${url.startsWith("/") ? "" : "/"}${url}`;
    try {
      console.log("[WS] connecting by URL:", lastUrl);
      ws = new WebSocket(lastUrl);
      bindSocket();
    } catch (error) {
      connected = false;
      console.error("[WS] connectByUrl failed:", error);
      scheduleReconnect();
    }
  };

  // --- API pública ---
  const on = (event, callback) => {
    addListener(event, callback);
    // Devuelve función para desuscribirse
    return () => removeListener(event, callback);
  };

  const off = (event, callback) => {
    removeListener(event, callback);
  };

  const send = (obj) => {
    try {
      if (ws && connected) {
        ws.send(JSON.stringify(obj));
      } else {
        console.warn("[WS] No conectado. Mensaje no enviado.");
      }
    } catch (e) {
      console.error("[WS] send error:", e);
    }
  };

  const disconnect = () => {
    shouldReconnect = false;
    try {
      ws?.close();
    } catch {}
    ws = null;
    connected = false;
    console.log("[WS] disconnected manually");
  };

  return {
  connect,        // connect(gameId)
    connectByUrl,   // usado por InGame.jsx
    disconnect,
    on,
    off,
    send,
    get isConnected() {
      return connected;
    },
  };
};
