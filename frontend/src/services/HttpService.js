// src/services/HttpService.js
const createHttpService = () => {
  // Mantengo el baseUrl de dev para no sorprender en este PR
  const baseUrl = 'http://127.0.0.1:8000/api';

  const request = async (endpoint, options = {}) => {
    const url = `${baseUrl}${endpoint}`;
    const config = {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    };

    const res = await fetch(url, config);

    if (!res.ok) {
      const err = new Error(`HTTP error! status: ${res.status}`);
      err.status = res.status;
      err.endpoint = endpoint;
      try {
        err.payload = await res.json();
      } catch (_) {}
      throw err;
    }

    if (res.status === 204) return null;
    return res.json();
  };

  // === Players ===
  const createPlayer = (player) =>
    request("/players", { method: "POST", body: JSON.stringify(player) });

  // === Games ===
  const createGamePublic = (game) =>
    request("/games", { method: "POST", body: JSON.stringify(game) });

  // (mergep0) presente también en dev pero con otra forma; dejamos la simple
  const getGames = () =>
    request("/games", { method: "GET" });

  const joinGame = (game_id, player_id) =>
    request(`/games/${game_id}/join`, {
      method: "POST",
      body: JSON.stringify({ game_id, player_id }),
    });

  const startGame = (game_id, player_id) =>
    request(`/games/${game_id}/start`, {
      method: "POST",
      body: JSON.stringify({ game_id, player_id }),
    });

  // === Reparto de cartas y secretos ===
  const dealGame = (game_id) =>
    request(`/games/${game_id}/deal`, { method: "POST" });

  const dealSecrets = (game_id) =>
    request(`/games/${game_id}/deal_secrets`, { method: "POST" });

  // === Información de cartas y secretos ===
  const getCards = (player_id, game_id) =>
    request(
      `/player/cards/${player_id}?game_id=${encodeURIComponent(game_id)}`,
      { method: "GET" }
    );

  const getSecrets = (player_id, game_id) =>
    request(
      `/player/secrets/${player_id}?game_id=${encodeURIComponent(game_id)}`,
      { method: "GET" }
    );

  // === Mazo y descarte ===
  const getRegularDeck = (game_id) =>
    request(`/games/${game_id}/mazos`, { method: "GET" });

  // === Turno actual ===
  const getTurn = (game_id) =>
    request(`/games/turn/${game_id}`, { method: "GET" });

  // === Acciones de turno ===
  const skipAction = (gameId, playerId) =>
    request(`/games/${gameId}/skip_action`, {
      method: "POST",
      body: JSON.stringify({ player_id: playerId }),
    });

  // dev usa EndTurn; dejamos alias endTurn para no romper ni uno ni otro
  const EndTurn = (game_id, player_id) =>
    request(`/games/${game_id}/turns/end`, {
      method: "POST",
      body: JSON.stringify({ player_id }),
    });
  const endTurn = EndTurn; // alias

  // === Cartas: descarte / draft / robar ===
  const discardCard = (game_id, player_id, card_name) =>
    request(`/games/${game_id}/${player_id}/descarte`, {
      method: "POST",
      body: JSON.stringify({ card_id: card_name }),
    });

  const draftCard = (gameId, playerId, cardName) =>
    request(`/games/${gameId}/draft/${playerId}/${cardName}`, {
      method: "POST",
    });

  const drawCardFromDeck = (game_id, player_id) =>
    request(`/games/${game_id}/players/${player_id}/draw`, {
      method: "POST",
    });

  // === Sets y jugabilidad (mergep0) ===
  const playCard = (gameId, playerId, cardName, body = {}) =>
    request(`/games/${gameId}/${playerId}/${cardName}/play_card`, {
      method: "POST",
      body: JSON.stringify(body),
    });

  // mismo endpoint, dos nombres por compatibilidad
  const getSets = (gameId) =>
    request(`/games/${gameId}/sets`, { method: "GET" });
  const watchSets = (game_id) =>
    request(`/games/${game_id}/sets`, { method: "GET" });

  const canPlayCard = (gameId, playerId, cardName) =>
    request(`/games/${gameId}/${playerId}/${cardName}/can_play_card`, {
      method: "GET",
    });

  // === Pila de descarte / selección (dev) ===
  const getWatchDiscardPile = (game_id, player_id) =>
    request(`/games/${game_id}/watch_discard_pile/${player_id}`, {
      method: "GET",
    });

  const postSelectedCard = (game_id, player_id, card_id) =>
    request(`/games/${game_id}/selected_card_in_hand/${player_id}`, {
      method: "POST",
      body: JSON.stringify({ card_id }),
    });

  return {
    request,
    // players/games
    createPlayer,
    createGamePublic,
    getGames,
    joinGame,
    startGame,
    // reparto
    dealGame,
    dealSecrets,
    // info
    getCards,
    getSecrets,
    // mazo/turno
    getRegularDeck,
    getTurn,
    // acciones
    skipAction,
    EndTurn,
    endTurn, // alias
    // cartas
    discardCard,
    draftCard,
    drawCardFromDeck,
    // sets/jugabilidad
    playCard,
    getSets,   // mismo endpoint que watchSets
    watchSets, // alias por compatibilidad con dev
    canPlayCard,
    // descarte/selección
    getWatchDiscardPile,
    postSelectedCard,
  };
};

export { createHttpService };
