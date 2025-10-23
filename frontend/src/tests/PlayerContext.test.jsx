import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import React from "react";
import { PlayerProvider, usePlayer } from "../containers/App/PlayerContext";

// Componente de prueba que usa el contexto
function TestComponent() {
  const { player, updatePlayer } = usePlayer();

  return (
    <>
      <p>{player ? player.name : "sin jugador"}</p>
      <button onClick={() => updatePlayer({ name: "Juan" })}>Actualizar</button>
    </>
  );
}

describe("PlayerContext", () => {
  it("actualiza el nombre del jugador", () => {
    render(
      <PlayerProvider>
        <TestComponent />
      </PlayerProvider>
    );

    // Al inicio muestra sin jugador
    expect(screen.getByText("sin jugador")).toBeInTheDocument();

    // Hacemos clic en el botón
    fireEvent.click(screen.getByText("Actualizar"));

    // Verificamos que cambió a "Juan"
    expect(screen.getByText("Juan")).toBeInTheDocument();
  });
});
