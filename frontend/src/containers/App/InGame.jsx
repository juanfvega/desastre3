// src/containers/App/InGame.jsx
import "./secrets-new.css";
import "./InGame.css";
import React, { useEffect, useState, useRef, useMemo } from "react";
import SecretsModal from "../../components/SecretsModal";
import TurnInfo from "../../components/TurnInfo";
import DisplayCards from "./DisplayCards";
import ViewRegularAndDiscardDecks from "./ViewRegularAndDiscardDecks";
import DrawFromDeck from "./DrawFromDeck";
import { useLocation } from "react-router-dom";
import { createHttpService } from "../../services/HttpService";
import { usePlayer } from "./PlayerContext";
import { createWSService } from "../../services/wsService";
import { getSeatPositions, getOtherPlayers } from "./tableLayout";
import EndTurnButton from "../../components/EndTurnButton";
import EndGameModal from "../../components/EndGameModal";
import CardDraftDisplay from "../../components/CardDraftDisplay";
import CardDraftDetail from "../../components/CardDraftDetail";

// DEV extras
import SetsModal from "./SetModal";
import WatchDiscardPile from "./WatchDiscardPile";

export default function InGame() {
  console.log("[InGame] render");

  // UI / modales
  const [isEndGameModalOpen, setIsEndGameModalOpen] = useState(false);
  const [winnerName, setWinnerName] = useState("");
  const [isSecretsModalOpen, setIsSecretsModalOpen] = useState(false);
  const [isSetsModalOpen, setIsSetsModalOpen] = useState(false);

  // Mano / draft
  const [cards, setCards] = useState([]);
  const [cardDraft, setCardDraft] = useState([]);
  const [isDraftModalOpen, setIsDraftModalOpen] = useState(false);
  const [selectedDraftCard, setSelectedDraftCard] = useState(null);

  // Turno / conexión
  const [currentTurnPlayer, setCurrentTurnPlayer] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentTurn, setCurrentTurn] = useState(null);

  // Secrets
  const [mySecrets, setMySecrets] = useState([
    { kind: null, revealed: false },
    { kind: null, revealed: false },
    { kind: null, revealed: false },
  ]);

  // Deck (estado fuente para ViewRegularAndDiscardDecks)
  const [deckInfo, setDeckInfo] = useState({ countMazo: 0, descarteVisible: [] });
  // Derivados (por si los usa otra UI)
  const [regularDeckCount, setRegularDeckCount] = useState(0);
  const [discardPile, setDiscardPile] = useState([]);

  // Turn state
  const [turnState, setTurnState] = useState({
    phase: "action",
    lastAction: "none",
    canEndTurn: false,
    canExecuteAction: true,
    mustDiscard: false,
  });

  // WatchDiscardPile
  const [loadingWatchDiscardPile, setLoadingWatchDiscardPile] = useState(false);
  const [cardsFromDiscardPile, setCardsFromDiscardPile] = useState([]);
  const [showModal, setShowModal] = useState(false);

  // Datos base / servicios
  const [gameData, setGameData] = useState(null);
  const location = useLocation();
  const { player } = usePlayer();

  // === Proxy de HttpService con logs para TODAS las llamadas ===
  const httpService = useMemo(() => {
    const raw = createHttpService();
    return new Proxy(raw, {
      get(target, prop, receiver) {
        const value = Reflect.get(target, prop, receiver);
        if (typeof value === "function") {
          return async (...args) => {
            try {
              console.log(`[API] ${String(prop)} >`, ...args);
              const res = await value.apply(target, args);
              console.log(`[API] ${String(prop)} <`, res);
              return res;
            } catch (e) {
              console.error(`[API] ${String(prop)} !`, e);
              throw e;
            }
          };
        }
        return value;
      },
    });
  }, []);

  const wsServiceRef = useRef(createWSService());
  const playersRef = useRef(location.state?.list_players);

  // Flags por partida
  const dealFlagKey = useMemo(
    () => (gameData?.game_id ? `dealAlreadyTriggered_${gameData.game_id}` : null),
    [gameData?.game_id]
  );
  const secretsFlagKey = useMemo(
    () => (gameData?.game_id ? `dealSecretsTriggered_${gameData.game_id}` : null),
    [gameData?.game_id]
  );
  const getFlag = (key) => (key ? window[key] : undefined);
  const setFlag = (key, val) => {
    if (!key) return;
    window[key] = val;
  };

  // === Anti doble-acción de draw (guard)
  const isDrawingRef = useRef(false);

  // === Dedup de deck_update
  const lastDeckHashRef = useRef("");

  // === Ajuste de conteo visible (para evitar -4 en refill de draft)
  const lastCountRef = useRef(0);
  const prevDraftLenRef = useRef(0);
  const inDrawWindowRef = useRef(false);

  // === Contadores / huellas de eventos WS (debug)
  const wsSeen = useRef({ counts: {}, lastAt: {}, lastHashes: {} });
  const hashPayload = (obj) => {
    try {
      return JSON.stringify(obj);
    } catch {
      return String(obj);
    }
  };
  const seen = (name, payload) => {
    wsSeen.current.counts[name] = (wsSeen.current.counts[name] || 0) + 1;
    wsSeen.current.lastAt[name] = Date.now();
    wsSeen.current.lastHashes[name] = hashPayload(payload);
    console.log(`[WS][COUNT] ${name} #${wsSeen.current.counts[name]}`, payload);
  };

  // === Sincronizar gameData con localStorage
  useEffect(() => {
    if (location.state) {
      console.log("[INIT] gameData desde location.state", location.state);
      localStorage.setItem("gameData", JSON.stringify(location.state));
      setGameData(location.state);
    } else {
      const saved = localStorage.getItem("gameData");
      if (saved) {
        console.log("[INIT] gameData desde localStorage");
        setGameData(JSON.parse(saved));
      }
    }
  }, [location.state]);

  // === Primer jugador para pintar turno
  useEffect(() => {
    if (gameData?.first_player) {
      console.log("[TURN] first_player =", gameData.first_player);
      setCurrentTurn(gameData.first_player);
    }
  }, [gameData]);

  // === WatchDiscardPile flag
  useEffect(() => {
    if (gameData?.game_id && player?.player_id) {
      setLoadingWatchDiscardPile(true);
    }
  }, [gameData?.game_id, player?.player_id]);

  // === Helpers
  const myId =
    sessionStorage.getItem("current_player_id") || player?.player_id || null;

  const setSecretsFromResponse = (arr) => {
    console.log("[SECRETS] setSecretsFromResponse raw:", arr);
    const normalized = Array.isArray(arr) ? arr : [];
    const first =
      normalized.length > 0
        ? {
            kind: normalized[0].secret ?? normalized[0].kind ?? null,
            revealed: Boolean(normalized[0].revealed),
          }
        : { kind: null, revealed: false };
    const final = [
      first,
      { kind: "inocente", revealed: false },
      { kind: "inocente", revealed: false },
    ];
    console.log("[SECRETS] final:", final);
    setMySecrets(final);
  };

  const fetchMySecrets = async (opts = { once: false }) => {
    if (!myId || !gameData?.game_id) return;
    try {
      console.log("[SECRETS] fetchMySecrets -> GET");
      const data = await httpService.getSecrets(myId, gameData.game_id);
      setSecretsFromResponse(data);
    } catch (e) {
      if (e?.status === 404 && !opts.once) {
        console.warn("[SECRETS] 404; reintento único en 1s");
        setTimeout(() => fetchMySecrets({ once: true }), 1000);
      } else {
        console.warn("[SECRETS] No fue posible obtener secretos:", e);
      }
    }
  };

  const refreshCardsForMe = async () => {
    if (!player?.player_id || !gameData?.game_id) return;
    try {
      console.log("[HAND] refreshCardsForMe -> GET");
      const fetched = await httpService.getCards(
        player.player_id,
        gameData.game_id
      );
      setCards(fetched);
      console.log("[HAND] cartas =", fetched);
    } catch (err) {
      console.error("[HAND] Error al obtener cartas:", err);
    }
  };

  const refreshDeck = async () => {
    if (!gameData?.game_id) return;
    try {
      console.log("[DECK] refreshDeck -> GET");
      const info = await httpService.getRegularDeck(gameData.game_id);
      console.log("[DECK] info =", info);
      const top = info?.descarteVisible?.at(-1) || null;
      const next = {
        countMazo: Number(info?.countMazo || 0),
        descarteVisible: top ? [top] : [],
      };
      setDeckInfo(next);
      setRegularDeckCount(next.countMazo);
      setDiscardPile(next.descarteVisible);

      lastDeckHashRef.current = JSON.stringify(next); // sincroniza el hash base
      lastCountRef.current = next.countMazo;          // sync para suavizado
      console.log("[DECK][SYNC] lastCountRef =", lastCountRef.current);
    } catch (e) {
      console.warn("[DECK] No fue posible obtener mazo:", e);
      setDeckInfo({ countMazo: 0, descarteVisible: [] });
    }
  };

  // === Hand para DrawFromDeck
  const fetchHand = (playerId, gameId) => {
    if (!playerId || !gameId) return;
    console.log("[HAND] fetchHand -> GET", { playerId, gameId });
    httpService
      .getCards(playerId, gameId)
      .then((fetchedCards) => {
        console.log("[HAND] fetchHand OK", fetchedCards);
        setCards(fetchedCards);
      })
      .catch((err) =>
        console.error("[HAND] Error al obtener cartas en fetchHand", err)
      );
  };

  // === Discard handler (dev/mergep0 compatible con CardModal.jsx) ===
  const handleDiscardAction = async (card, closeModal) => {
    const card_name = card?.name;
    const gameId = gameData?.game_id;
    const playerId = player?.player_id;

    if (!card_name || !gameId || !playerId) {
      console.warn("[DISCARD] faltan datos", { card_name, gameId, playerId });
      closeModal?.();
      return;
    }

    try {
      console.log("[DISCARD] POST", { gameId, playerId, card_name });
      await httpService.discardCard(gameId, playerId, card_name);

      // Actualizar mano local
      setCards((prevCards) => {
        const idx = prevCards.findIndex((c) => c.name === card_name);
        if (idx > -1) {
          const cp = [...prevCards];
          cp.splice(idx, 1);
          console.log("[DISCARD] removida de mano, nueva mano:", cp);
          return cp;
        }
        return prevCards;
      });

      closeModal?.();
    } catch (error) {
      console.error("[DISCARD] Error al descartar la carta:", error);
      alert("Fallo al descartar la carta. Inténtalo de nuevo.");
    }
  };

  // === Guard de draw (si tu DrawFromDeck lo soporta, pasamos callbacks)
  const onBeforeDraw = () => {
    if (isDrawingRef.current) {
      console.warn("[DRAW] ignorado: ya hay un draw en curso");
      return false;
    }
    isDrawingRef.current = true;
    inDrawWindowRef.current = true; // abrimos ventana para detectar refill
    console.log("[DRAW] init (guard ON) | window ON");
    return true;
  };
  const onAfterDraw = () => {
    isDrawingRef.current = false;
    // cerramos la ventana luego de un breve tiempo para capturar cascada de refill
    setTimeout(() => {
      inDrawWindowRef.current = false;
      console.log("[DRAW] window OFF");
    }, 400);
    console.log("[DRAW] done (guard OFF, window 400ms)");
  };
  const handleDrawFromDeck = async (playerId, gameId) => {
    // Si tu DrawFromDeck ya hace el POST internamente, este handler será solo el “success”.
    try {
      await fetchHand(playerId, gameId);
    } finally {
      if (isDrawingRef.current) onAfterDraw();
    }
  };

  // === Pull inicial por si no llegan eventos
  useEffect(() => {
    if (!gameData?.game_id || !player?.player_id) return;
    console.log("[INIT] pull suave -> refreshDeck + fetchMySecrets");
    refreshDeck();
    fetchMySecrets({ once: true });
  }, [gameData?.game_id, player?.player_id]);

  // === WS principal (único)
  useEffect(() => {
    if (!gameData?.game_id || !player?.player_id) return;

    const wsService = wsServiceRef.current;
    console.log("[WS] connecting to game", gameData.game_id);
    wsService.connect(gameData.game_id);
    setIsConnected(true);

    wsService.onAny &&
      wsService.onAny((msg) => {
        console.log("[WS][GLOBAL] Mensaje recibido:", msg);
      });

    const handleCardsDealt = async (data) => {
      if (data?.event === "cards_dealt" && data?.game_id === gameData.game_id) {
        seen("cards_dealt", {});
        await refreshCardsForMe();
      }
    };

    const handleSecretsDealt = async (data) => {
      if (data?.event === "secrets_dealt" && data?.game_id === gameData.game_id) {
        seen("secrets_dealt", {});
        await fetchMySecrets({ once: true });
      }
    };

    // DEV: deck_update { draw_pile_count, top_discard, card_draft? }
    const handleDeckUpdate = (data) => {
      if (data?.event !== "deck_update" || data?.game_id !== gameData.game_id)
        return;

      const payload = {
        draw_pile_count: data.draw_pile_count,
        top_discard: data.top_discard,
        draftLen: Array.isArray(data.card_draft) ? data.card_draft.length : 0,
      };
      seen("deck_update", payload);

      const serverCount = Number(data.draw_pile_count || 0);
      const top = data.top_discard || null;
      const nextDraftLen = payload.draftLen;

      // === Lógica de suavizado (-4 -> mostrar -1 durante ventana de draw)
      const prevCount = lastCountRef.current ?? serverCount;
      const delta = serverCount - prevCount; // negativo = bajó
      const draftGrew = nextDraftLen > prevDraftLenRef.current;
      let visibleCount = serverCount;

      console.log("[DECK][RAW]", {
        serverCount,
        prevCount,
        delta,
        draftGrew,
        inDrawWindow: inDrawWindowRef.current,
        prevDraftLen: prevDraftLenRef.current,
        nextDraftLen,
      });

      if (inDrawWindowRef.current && delta <= -2 && draftGrew) {
        // Reposición del draft + carta robada => mostrar -1
        visibleCount = prevCount - 1;
        console.log(
          "[DECK][SMOOTH] refill detectado: serverCount=",
          serverCount,
          "prevCount=",
          prevCount,
          "=> visibleCount=",
          visibleCount
        );
      }

      const next = { countMazo: visibleCount, descarteVisible: top ? [top] : [] };
      const nextHash = JSON.stringify(next);

      if (nextHash === lastDeckHashRef.current) {
        console.log("[WS] deck_update (sin cambios) -> no-op");
      } else {
        lastDeckHashRef.current = nextHash;
        setRegularDeckCount(visibleCount);
        setDiscardPile(next.descarteVisible);
        setDeckInfo(next);
        console.log("[DECK][APPLY]", next);
      }

      // siempre actualizamos draft visual
      if (Array.isArray(data.card_draft)) setCardDraft(data.card_draft);

      // actualizar refs para próxima comparación
      lastCountRef.current = visibleCount;
      prevDraftLenRef.current = nextDraftLen;
      console.log("[DECK][REFS] lastCountRef=", lastCountRef.current, "prevDraftLenRef=", prevDraftLenRef.current);
    };

    // LEGACY: deck_updated { regularCount, discard }
    const handleDeckUpdatedLegacy = (data) => {
      if (data?.event !== "deck_updated" || data?.game_id !== gameData.game_id)
        return;
      seen("deck_updated", { regularCount: data.regularCount, hasDiscard: !!data.discard });
      const next = {
        countMazo: Number(data.regularCount || 0),
        descarteVisible: data.discard ? [data.discard] : [],
      };
      lastDeckHashRef.current = JSON.stringify(next);
      setDeckInfo(next);

      // sync refs
      lastCountRef.current = next.countMazo;
      console.log("[DECK][LEGACY][SYNC] lastCountRef =", lastCountRef.current);
    };

    const handleDiscardUpdated = (data) => {
      if (data?.event !== "discard_updated" || data?.game_id !== gameData.game_id)
        return;
      seen("discard_updated", { count: (data.discards_cards || []).length });
      const discard_cards = data.discards_cards;
      setDiscardPile(discard_cards || []);
    };

    const handleTurnUpdate = (data) => {
      if (data?.event !== "turn.update") return;
      seen("turn.update", {
        phase: data.phase,
        lastAction: data.lastAction,
        canEndTurn: data.canEndTurn,
        active: data.activePlayerId,
      });
      const phase = data.phase ?? "action";
      const lastAction = data.lastAction ?? "none";
      const canEndTurn = !!data.canEndTurn;
      const derivedMustDiscard =
        phase === "discard_required" ||
        (phase === "ready_to_end" && lastAction === "skip_action" && !canEndTurn);
      setCurrentTurnPlayer({
        id: data.activePlayerId,
        name: data.activePlayerName ?? data.activePlayerId,
        avatar: data.activePlayerAvatar,
      });
      setTurnState({
        phase,
        lastAction,
        canEndTurn,
        canExecuteAction: phase === "action",
        mustDiscard: derivedMustDiscard,
      });
      console.log("[TURN][STATE]", {
        phase,
        lastAction,
        canEndTurn,
        canExecuteAction: phase === "action",
        mustDiscard: derivedMustDiscard,
      });
    };

    const handleTurnChanged = (data) => {
      if (data?.type !== "game.turn.changed") return;
      seen("game.turn.changed", { current: data.currentTurnPlayerId });
      const pid = data.currentTurnPlayerId;
      const info = playersRef.current?.find((p) => p.id === pid);
      setCurrentTurnPlayer(info || { id: pid, name: pid, avatar: null });
      console.log("[TURN][CHANGED] active =", pid);
    };

    const handleCardDraftUpdate = (data) => {
      if (data?.event !== "card_draft_updated") return;
      seen("card_draft_updated", { count: (data?.payload?.cards || []).length });
      const safe = data?.payload?.cards;
      if (Array.isArray(safe)) setCardDraft(safe);
      console.log("[DRAFT][UPDATE] len =", (safe || []).length);
    };

    const handleEndGame = (payload) => {
      if (payload?.event === "game_end" && payload?.game_id === gameData.game_id) {
        seen("game_end", { winner: payload.winner });
        setWinnerName(payload.winner || "Asesino");
        setIsEndGameModalOpen(true);
      }
    };

    // Suscripciones
    wsService.on("cards_dealt", handleCardsDealt);
    wsService.on("secrets_dealt", handleSecretsDealt);
    wsService.on("deck_update", handleDeckUpdate);
    wsService.on("deck_updated", handleDeckUpdatedLegacy);
    wsService.on("discard_updated", handleDiscardUpdated);
    wsService.on("turn.update", handleTurnUpdate);
    wsService.on("game.turn.changed", handleTurnChanged);
    wsService.on("card_draft_updated", handleCardDraftUpdate);
    wsService.on("game_end", handleEndGame);

    // Host: deal único por partida
    const iAmHost = String(player.player_id) === String(gameData.host_id);
    console.log("[HOST?]", { iAmHost, my: String(player.player_id), host: String(gameData.host_id) });

    if (iAmHost) {
      if (!getFlag(dealFlagKey)) {
        console.log("[HOST] dealGame(): disparando (flag off) ->", dealFlagKey);
        setFlag(dealFlagKey, true);
        httpService
          .dealGame(gameData.game_id)
          .then(async () => {
            console.log("[HOST] dealGame OK");
            await refreshDeck();
          })
          .catch((err) => {
            console.error("[HOST] dealGame ERROR", err);
            setFlag(dealFlagKey, false);
          });
      } else {
        console.log("[HOST] dealGame(): omitido (flag on) ->", dealFlagKey);
      }

      if (!getFlag(secretsFlagKey)) {
        console.log("[HOST] dealSecrets(): disparando (flag off) ->", secretsFlagKey);
        setFlag(secretsFlagKey, true);
        httpService
          .dealSecrets(gameData.game_id)
          .then(async () => {
            console.log("[HOST] dealSecrets OK");
            await fetchMySecrets({ once: true });
          })
          .catch((err) => {
            console.error("[HOST] dealSecrets ERROR", err);
            setFlag(secretsFlagKey, false);
          });
      } else {
        console.log("[HOST] dealSecrets(): omitido (flag on) ->", secretsFlagKey);
      }
    } else {
      console.log("[WS] No soy host; espero broadcasts.");
    }

    return () => {
      console.log("[WS] cleanup: desuscribiendo handlers y marcando desconectado");
      wsService.off("cards_dealt", handleCardsDealt);
      wsService.off("secrets_dealt", handleSecretsDealt);
      wsService.off("deck_update", handleDeckUpdate);
      wsService.off("deck_updated", handleDeckUpdatedLegacy);
      wsService.off("discard_updated", handleDiscardUpdated);
      wsService.off("turn.update", handleTurnUpdate);
      wsService.off("game.turn.changed", handleTurnChanged);
      wsService.off("card_draft_updated", handleCardDraftUpdate);
      wsService.off("game_end", handleEndGame);
      setIsConnected(false);
    };
  }, [gameData?.game_id, player?.player_id, httpService, dealFlagKey, secretsFlagKey]);

  // === Hidratación inicial de turno
  useEffect(() => {
    if (!gameData?.game_id) return;
    console.log("[TURN] GET /turn hidratación inicial");
    httpService
      .getTurn(gameData.game_id)
      .then((res) => {
        const pid = res.currentTurnPlayerId;
        if (!pid) return;
        const info = gameData.list_players?.find((p) => p.id === pid);
        setCurrentTurnPlayer(info || { id: pid, name: pid, avatar: null });
        setTurnState((prev) => ({
          ...prev,
          phase: res.phase || "action",
          lastAction: res.lastAction || "none",
        }));
        console.log("[TURN][INIT]", { pid, phase: res.phase, lastAction: res.lastAction });
      })
      .catch((err) => console.error("[TURN] Error hidratando turno:", err));
  }, [gameData?.game_id, gameData?.list_players, httpService]);

  // === Skip action
  const handleSkipTurn = async () => {
    if (!gameData?.game_id || !myId) return;
    try {
      console.log("[TURN] skipAction POST", { gameId: gameData.game_id, myId });
      await httpService.skipAction(gameData.game_id, myId);
      await refreshCardsForMe();
    } catch (err) {
      console.error("[TURN] Error al omitir turno:", err);
      alert("No se pudo omitir el turno. Ver consola.");
    }
  };

  // === WatchDiscardPile
  const handleOpenModal = async () => {
    try {
      console.log("[ASHES] GET watchDiscardPile");
      const response = await httpService.getWatchDiscardPile(
        gameData.game_id,
        player.player_id
      );
      setCardsFromDiscardPile(response);
      setShowModal(true);
    } catch (error) {
      console.error("[ASHES] Error al obtener cartas de descarte:", error);
    }
  };

  // === UI derived (secrets)
  const secretCards = mySecrets.map((s, i) => ({
    id: i + 1,
    name: s.kind ?? "Secreto sin asignar",
    type: "secreto",
    description:
      s.kind === "asesino"
        ? "Sos el asesino."
        : s.kind === "cómplice"
        ? "Sos el cómplice."
        : s.kind === "inocente"
        ? "Sos inocente."
        : "Aún no se asignó tu secreto.",
    condition: s.revealed ? "Revelado" : "Oculto",
  }));

  const myTurn =
    currentTurnPlayer?.id &&
    myId &&
    String(currentTurnPlayer.id) === String(myId);

  const turnInfoState = {
    canExecuteAction: turnState.canExecuteAction && myTurn,
    actionExecuted: turnState.lastAction !== "none",
    state: myTurn ? "can-end" : "waiting",
    lastAction: turnState.lastAction,
  };

  const otherPlayers = useMemo(
    () => getOtherPlayers(gameData?.list_players || [], myId),
    [gameData, myId]
  );
  const seatPositions = useMemo(
    () => getSeatPositions(otherPlayers.length),
    [otherPlayers.length]
  );

  console.log("[DERIVED]", {
    myTurn,
    countMazo: deckInfo.countMazo,
    descarteTop: deckInfo.descarteVisible?.[0],
    draftLen: cardDraft.length,
  });

  return (
    <div className="se-app">
      <div className="deck-center-element">
        {gameData && (
          <ViewRegularAndDiscardDecks
            deckInfo={deckInfo}
            game_id={gameData.game_id}
          />
        )}
      </div>

      <div
        className={`game-table-container${
          currentTurn === player?.player_id ? " my-turn" : ""
        }`}
      >
        <div className="se-table">
          <img src="/secrets/wood.jpg" alt="Mesa" />
          {otherPlayers.map((p, i) => {
            const pos = seatPositions[i];
            return (
              <div
                key={p.id}
                className="se-seat"
                style={{
                  top: pos.top,
                  left: pos.left,
                  transform: pos.transform,
                }}
              >
                <span className="se-seat-name">{p.name}</span>
                <span className="se-seat-badge">Jugador</span>
              </div>
            );
          })}
        </div>

        <div className="draft-area">
          <CardDraftDisplay
            draftCards={cardDraft}
            onCardSelect={
              setSelectedDraftCard
                ? (c) => {
                    console.log("[DRAFT] select", c);
                    setSelectedDraftCard(c);
                    setIsDraftModalOpen(true);
                  }
                : undefined
            }
          />
        </div>

        {/* Tus cartas */}
        <div className="display-containter" style={{ zIndex: 9000 }}>
          <DisplayCards
            cards={cards}
            onClickLookIntoAshes={handleOpenModal}
            setCards={setCards}
            gameData={gameData}
            onDiscardAction={handleDiscardAction}
            deckInfo={deckInfo}
            player={player}
            // mergep0 extras (CardModal nuevo)
            gameId={gameData?.game_id}
            playerId={player?.player_id}
            onHandRefresh={refreshCardsForMe}
          />

          {showModal && (
            <WatchDiscardPile
              cards={cardsFromDiscardPile}
              showModal={showModal}
              setShowModal={setShowModal}
              gameData={gameData}
              player={player}
              setCards={setCards}
            />
          )}
        </div>
      </div>

      <div className="game-turn-info game-overlay-element">
        <TurnInfo
          currentPlayer={currentTurnPlayer}
          isConnected={isConnected}
          turnState={turnInfoState}
        />
      </div>

      <div className="game-buttons-container game-overlay-element">
        <button
          onClick={() => setIsSecretsModalOpen(true)}
          className="game-button game-button-secrets"
        >
          Ver mis secretos ({secretCards.length})
        </button>

        {currentTurn === player?.player_id && (
          <button onClick={handleSkipTurn} className="game-button game-button-skip">
            No Ejecutar Acción
          </button>
        )}

        {/* Draw desde mazo cuando es tu turno */}
        {gameData &&
          currentTurn &&
          player?.player_id &&
          String(currentTurn) === String(player.player_id) && (
            <DrawFromDeck
              playerId={player.player_id}
              gameId={gameData.game_id}
              // Guard/trace: si el hijo los soporta, evita doble click
              onBeforeDraw={onBeforeDraw}
              onAfterDraw={onAfterDraw}
              // Success handler (si el hijo llama backend interno)
              onDrawSuccess={handleDrawFromDeck}
              debug={(() => {
                console.log("[DrawFromDeck] Render", {
                  playerId: player.player_id,
                  gameId: gameData.game_id,
                });
                return true;
              })()}
            />
          )}

        {/* End Turn */}
        {gameData && currentTurn && player?.player_id && (
          <EndTurnButton
            handCompleted={true}
            currentPlayerPlayEvent={true}
            currentPlayerPlaySet={true}
            currentPlayerAddOneDetectiveCard={true}
            playerId={player.player_id}
            gameId={gameData.game_id}
            isMyTurn={String(currentTurn) === String(player.player_id)}
            setCurrentTurn={setCurrentTurn}
            wsService={wsServiceRef.current}
            className="game-button game-button-end-turn"
            debug={(() => {
              console.log("[EndTurnButton] Render", {
                playerId: player.player_id,
                gameId: gameData.game_id,
                isMyTurn: String(currentTurn) === String(player.player_id),
              });
              return true;
            })()}
          />
        )}
      </div>

      {/* Modales sueltos */}
      <CardDraftDetail
        isOpen={isDraftModalOpen}
        onClose={() => setIsDraftModalOpen(false)}
        card={selectedDraftCard}
        onDraftAction={async (c) => {
          console.log("[DRAFT] action", c);
          await (async () => {
            if (!gameData?.game_id || !player?.player_id || !c?.name) return;
            if (cards.length >= 6) {
              alert("No puedes tomar esta carta del draft: tu mano ya tiene 6 cartas.");
              setIsDraftModalOpen(false);
              return;
            }
            try {
              await httpService.draftCard(gameData.game_id, player.player_id, c.name);
              setIsDraftModalOpen(false);
              await refreshCardsForMe();
            } catch (error) {
              console.error("[DRAFT] Error al tomar carta del draft:", error);
              alert(`Fallo al tomar la carta del draft. ${error?.detail || "Error desconocido."}`);
            }
          })();
        }}
      />

      <SecretsModal
        isOpen={isSecretsModalOpen}
        onClose={() => setIsSecretsModalOpen(false)}
        secretCards={secretCards}
      />

      {/* Botón y modal de Sets */}
      <button
        onClick={() => setIsSetsModalOpen(true)}
        className="game-button game-button-view-sets"
      >
        Ver Sets
      </button>

      {gameData && (
        <SetsModal
          isOpen={isSetsModalOpen}
          onClose={() => setIsSetsModalOpen(false)}
          gameId={gameData?.game_id}
          playerId={player?.player_id}
          // TIP: si este modal llama a httpService.playSet, el proxy ya lo loguea.
          // Si no, agregá logs ahí (phase/canExecuteAction/myTurn) antes de enviar.
        />
      )}

      <EndGameModal
        isOpen={isEndGameModalOpen}
        winnerName={winnerName}
        onClose={() => setIsEndGameModalOpen(false)}
      />
    </div>
  );
}
