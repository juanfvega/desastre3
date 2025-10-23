import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import DrawFromDeck from "../containers/App/DrawFromDeck";

// 👇 Cambia jest.mock → vi.mock
vi.mock("../services/HttpService", () => ({
  createHttpService: () => ({
    drawCardFromDeck: vi.fn(() => Promise.resolve({ message: "Cards drawn successfully" })),
  }),
}));

describe("DrawFromDeck", () => {
  it("llama a drawCardFromDeck y ejecuta onDrawSuccess al hacer clic", async () => {
    const mockOnDrawSuccess = vi.fn();

    render(<DrawFromDeck playerId="p1" gameId="g1" onDrawSuccess={mockOnDrawSuccess} />);

    const button = screen.getByRole("button", { name: /robar del mazo/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockOnDrawSuccess).toHaveBeenCalledWith("p1", "g1");
    });
  });
});
