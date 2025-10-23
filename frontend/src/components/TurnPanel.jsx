// components/TurnPanel.jsx
import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import { createHttpService } from "../services/HttpService";
import { createWSService } from "../services/wsService";
import TurnInfo from "./TurnInfo";
import ActionButton from "./ActionButton";
// import "./TurnPanel.css";

export default function TurnPanel({ gameId, myPlayerId }) {
  const http = useMemo(() => createHttpService(), []);
  const ws = useMemo(() => createWSService(), []);

  const [currentPlayer, setCurrentPlayer] = useState(null); // { id, name?, avatar? }
  const [turnState, setTurnState] = useState({
    phase: "action",         // "action" | "ready_to_end" | "discard_required"
    lastAction: "none",      // "none" | "played" | "discard" | "skip_action"
    canEndTurn: false,
    canExecuteAction: true,
    mustDiscard: false,
  });

  const mountedRef = useRef(false);
  const isActive = currentPlayer?.id && myPlayerId && String(currentPlayer.id) === String(myPlayerId);

  // ------ Helpers ------
  const applyTurnUpdate = (p, source = "unknown") => {
    if (!p) return;
    const phase = p.phase ?? "action";
    const lastAction = p.lastAction ?? "none";
    const canEndTurn = !!p.canEndTurn;

    const derivedMustDiscard =
      phase === "discard_required" ||
      (phase === "ready_to_end" && lastAction === "skip_action" && !canEndTurn);

    const nextPlayer = {
      id: p.activePlayerId,
      name: p.activePlayerName ?? p.activePlayerId,
      avatar: p.activePlayerAvatar ?? null,
    };

    console.log(`[TURN][APPLY from ${source}]`, {
      phase,
      lastAction,
      canEndTurn,
      derivedMustDiscard,
      activePlayerId: nextPlayer.id,
    });

    setCurrentPlayer(nextPlayer);
    setTurnState({
      phase,
      lastAction,
      canEndTurn,
      canExecuteAction: phase === "action",
      mustDiscard: derivedMustDiscard,
    });
  };

  // ------ Conexión WS + listeners ------
  useEffect(() => {
    if (!gameId) return;
    mountedRef.current = true;

    console.log("[TURNPANEL] WS connect ->", gameId);
    ws.connect(gameId);

    ws.onAny?.((msg) => {
      console.log("[WS][ANY][TurnPanel] raw:", msg);
    });

    const onTurnUpdate = (payload) => {
      const ev = payload?.event || payload?.type;
      if (ev !== "turn.update") return;
      if (payload?.game_id && String(payload.game_id) !== String(gameId)) {
        console.log("[WS][turn.update] ignorado por game_id", payload?.game_id, "actual", gameId);
        return;
      }
      console.log("[WS][turn.update] payload:", payload);
      applyTurnUpdate(
        {
          phase: payload.phase,
          lastAction: payload.lastAction,
          canEndTurn: payload.canEndTurn,
          activePlayerId: payload.activePlayerId,
          activePlayerName: payload.activePlayerName,
          activePlayerAvatar: payload.activePlayerAvatar,
        },
        "ws.turn.update"
      );
    };

    const onTurnChanged = (payload) => {
      const ev = payload?.event || payload?.type;
      if (ev !== "game.turn.changed") return;
      if (payload?.game_id && String(payload.game_id) !== String(gameId)) {
        console.log("[WS][game.turn.changed] ignorado por game_id", payload?.game_id, "actual", gameId);
        return;
      }
      console.log("[WS][game.turn.changed] payload:", payload);

      // Este evento a veces solo trae el nuevo playerId. Normalizamos para applyTurnUpdate
      applyTurnUpdate(
        {
          phase: "action",
          lastAction: "none",
          canEndTurn: false,
          activePlayerId: payload.currentTurnPlayerId ?? payload.nextPlayerId,
          activePlayerName: payload.currentTurnPlayerName ?? payload.nextPlayerName,
          activePlayerAvatar: payload.currentTurnPlayerAvatar ?? payload.nextPlayerAvatar,
        },
        "ws.game.turn.changed"
      );
    };

    const off1 = ws.on("turn.update", onTurnUpdate);
    const off2 = ws.on("game.turn.changed", onTurnChanged);

    // ------ Hidratación inicial (muy importante) ------
    (async () => {
      try {
        console.log("[TURNPANEL] GET /turn hidratación inicial");
        const res = await http.getTurn(gameId);
        console.log("[TURNPANEL] /turn <", res);

        const pid = res.currentTurnPlayerId;
        if (!pid) {
          console.warn("[TURNPANEL] /turn sin currentTurnPlayerId – quedamos esperando WS");
          return;
        }

        applyTurnUpdate(
          {
            phase: res.phase || "action",
            lastAction: res.lastAction || "none",
            canEndTurn: !!res.canEndTurn,
            activePlayerId: pid,
            activePlayerName: res.activePlayerName,
            activePlayerAvatar: res.activePlayerAvatar,
          },
          "http.getTurn"
        );
      } catch (e) {
        console.error("[TURNPANEL] Error hidratando turno:", e);
      }
    })();

    return () => {
      mountedRef.current = false;
      console.log("[TURNPANEL] cleanup WS listeners + disconnect");
      off1 && off1();
      off2 && off2();
      ws.disconnect?.();
    };
  }, [ws, http, gameId]);

  // ------ Acciones ------
  const handleNoAction = useCallback(async () => {
    try {
      console.log("[TURNPANEL] POST skipAction", { gameId, myPlayerId });
      await http.skipAction(gameId, myPlayerId);
      // El backend debería emitir 'turn.update' y/o 'deck_update'
    } catch (e) {
      console.error("[TURNPANEL] skip_action failed", e);
    }
  }, [http, gameId, myPlayerId]);

  // const handleEndTurn = useCallback(async () => {
  //   try {
  //     console.log("[TURNPANEL] POST endTurn", { gameId, myPlayerId });
  //     await http.endTurn(gameId, myPlayerId);
  //   } catch (e) {
  //     console.error("[TURNPANEL] end_turn failed", e);
  //   }
  // }, [http, gameId, myPlayerId]);

  return (
    <div className="turn-panel">
      <TurnInfo
        currentPlayer={currentPlayer}
        isConnected={true}
        turnState={{
          actionExecuted: turnState.lastAction !== "none",
          mustDiscard: turnState.mustDiscard,
          canEndTurn: turnState.canEndTurn,
          canExecuteAction: turnState.canExecuteAction,
          lastAction: turnState.lastAction,
        }}
      />

      {isActive && (
        <div className="turn-controls">
          <ActionButton
            onNoAction={handleNoAction}
            isVisible={turnState.phase === "action"}
            disabled={!turnState.canExecuteAction}
          />

          {/* Si habilitás terminar turno desde acá:
          <button
            onClick={handleEndTurn}
            disabled={!turnState.canEndTurn}
            className={`end-turn-btn ${turnState.canEndTurn ? "enabled" : "disabled"}`}
          >
            Terminar turno
          </button>
          */}
        </div>
      )}
    </div>
  );
}
