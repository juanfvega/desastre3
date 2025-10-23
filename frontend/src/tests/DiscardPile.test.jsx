import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import DiscardPile from "../../src/components/DiscardPile";


describe("DiscardPile", () => {
  const mockCards = [
    { type: "Detective", name: "poirot" },
    { type: "Detective", name: "marple" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Renderiza la carta de fondo (card_back_pile.png)", () => {
    render(<DiscardPile cards={[]} />);

    const backImage = screen.getByRole("img", { hidden: true });
    expect(backImage).toHaveAttribute("src", "/Cards/card_back_pile.png");
  });

  it(" Renderiza la cantidad correcta de cartas en la pila", () => {
    render(<DiscardPile cards={mockCards} />);

    const images = screen.getAllByRole("img");
    // 1 del fondo + 2 del mockCards
    expect(images.length).toBe(3);
  });

  it(" Cada carta genera correctamente el path y alt", () => {
    render(<DiscardPile cards={mockCards} />);

    expect(screen.getByAltText("Detective - poirot")).toHaveAttribute(
      "src",
      "/Cards/poirot.png"
    );
    expect(screen.getByAltText("Detective - marple")).toHaveAttribute(
      "src",
      "/Cards/marple.png"
    );
  });
});
