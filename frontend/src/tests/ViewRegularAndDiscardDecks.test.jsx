import React from "react";
import { render, screen } from "@testing-library/react";
import ViewRegularAndDiscardDecks from "../containers/App/ViewRegularAndDiscardDecks";

describe("ViewRegularAndDiscardDecks", () => {
  it("muestra el número de cartas del mazo regular", () => {
    render(<ViewRegularAndDiscardDecks regularDeckCount={5} discardPile={[]} />);
    
    const regularDeck = screen.getByTestId("regular-deck");
    expect(regularDeck).toHaveTextContent("5");
  });

  it("muestra las cartas del descarte cuando hay elementos", () => {
    const discard = [
      { type: "Detective", name: "Harley Quin" },
      { type: "Detective", name: "Poirot" },
    ];

    render(<ViewRegularAndDiscardDecks regularDeckCount={8} discardPile={discard} />);
    
    const discardPileEl = screen.getByTestId("discard-pile") || screen.getByText(/Cartas visibles: 2/i);
    expect(discardPileEl).toBeInTheDocument();
  });
});
