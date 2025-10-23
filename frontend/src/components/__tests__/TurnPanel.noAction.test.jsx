import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, test, expect, beforeEach, vi } from "vitest";
import TurnPanel from "../TurnPanel";

// --- mocks mínimos de servicios --- //
const mockSkipAction = vi.fn();
const mockConnect = vi.fn();
const mockDisconnect = vi.fn();
let wsHandlers = {};

vi.mock("../../services/HttpService", () => ({
  createHttpService: () => ({
    skipAction: (...args) => mockSkipAction(...args),
  }),
}));

vi.mock("../../services/wsService", () => ({
  createWSService: () => ({
    connect: (...args) => mockConnect(...args),
    disconnect: () => mockDisconnect(),
    on: (event, handler) => {
      wsHandlers[event] = handler;
      return () => delete wsHandlers[event];
    },
  }),
}));

// helper para simular evento "turn.update"
function emitTurnUpdate(payload) {
  const handler = wsHandlers["turn.update"];
  if (handler) handler(payload);
}

describe("TurnPanel - botón 'No ejecutar acción'", () => {
  const gameId = "game-1";
  const myPlayerId = "player-1";

  beforeEach(() => {
    vi.clearAllMocks();
    wsHandlers = {};
  });

  test("el jugador activo ve el botón y al hacer click llama a skipAction", async () => {
    render(<TurnPanel gameId={gameId} myPlayerId={myPlayerId} />);

    // Simula WS: soy el jugador activo, fase acción
    await act(async () => {
      emitTurnUpdate({
        activePlayerId: myPlayerId,
        phase: "action",
        lastAction: "none",
        canEndTurn: false,
      });
    });

    const button = screen.getByRole("button", { name: /No ejecutar acción/i });
    expect(button).toBeInTheDocument();

    // Click → llama al endpoint
    await act(async () => {
      fireEvent.click(button);
    });

    expect(mockSkipAction).toHaveBeenCalledWith(gameId, myPlayerId);
  });
});
