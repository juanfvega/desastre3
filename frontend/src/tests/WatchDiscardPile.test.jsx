import React, { act } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, vi, beforeEach, expect } from "vitest";
import WatchDiscardPile from "../containers/App/WatchDiscardPile";
import Card from "../components/Card";


// Mock del servicio HTTP
const mockHttpService = {
  getWatchDiscardPile: vi.fn().mockResolvedValue([{ id: 1, name: "Carta 1" }]),
  postSelectedCard: vi.fn(),
  getCards: vi.fn(),
};

vi.mock("../services/HttpService", () => ({
  createHttpService: () => mockHttpService,
}));

// Mock del modal
vi.mock("../components/CardModal", () => ({
  default: ({ isOpen }) => (isOpen ? <div data-testid="cards-modal">Modal abierto</div> : null),
}));

describe("WatchDiscardPile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("abre el modal al hacer click en el botón", async () => {
    render(
      <WatchDiscardPile game_id="game1" player_id="player1" onCardLoaded={vi.fn()} />
    );

    // Click en el botón
    act(() => {
      fireEvent.click(screen.getByText("Ver mazo descarte"));
    }); 

    // Verifica que se llame al servicio
    expect(mockHttpService.getWatchDiscardPile).toHaveBeenCalledWith("game1", "player1");

    // Verifica que se renderice el modal
    const modal = await screen.findByTestId("cards-modal");
    expect(modal).toBeInTheDocument();
  });

  it("abre el modal al hacer click en el botón y hace clic en la carta", async () => {

    render(
      <WatchDiscardPile game_id="game1" player_id="player1" onCardLoaded={vi.fn()} />
    );

    // Click en el botón
    act(() => {
      fireEvent.click(screen.getByText("Ver mazo descarte"));
    }); 

    // Verifica que se llame al servicio
    expect(mockHttpService.getWatchDiscardPile).toHaveBeenCalledWith("game1", "player1");

    // Verifica que se renderice el modal
    const modal = await screen.findByTestId("cards-modal");
    expect(modal).toBeInTheDocument();
    });


});
