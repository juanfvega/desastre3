// src/tests/Card.test.jsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Card from "../components/Card";

describe("Card", () => {
  const mockCard = {
    name: "detective_Holmes",
    image_id: "detective_Holmes"
  };

  it("Renderiza la carta correctamente", () => {
    const mockClick = vi.fn();

    render(<Card card={mockCard} onCardClick={mockClick} />);

    // 1. Comprueba que el contenedor existe
    const container = screen.getByRole("img", { name: /carta detective_holmes/i });
    expect(container).toBeInTheDocument();

    // 2. La imagen tiene src correcto
    expect(container.src).toContain("/Cards/detective_Holmes.png");
  });

  it("Llama a onCardClick al hacer click", () => {
    const mockClick = vi.fn();

    render(<Card card={mockCard} onCardClick={mockClick} />);

    const cardDiv = screen.getByAltText(/carta detective_holmes/i);
    fireEvent.click(cardDiv);

    expect(mockClick).toHaveBeenCalledTimes(1);
    expect(mockClick).toHaveBeenCalledWith(mockCard);
  });

  it("Retorna null y muestra error si no hay image_id ni name", () => {
    const mockCardInvalid = {};
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const { container } = render(<Card card={mockCardInvalid} onCardClick={() => {}} />);
    
    // El componente no debe renderizar nada
    expect(container.firstChild).toBeNull();

    // Debe mostrar mensaje de error
    expect(consoleErrorSpy).toHaveBeenCalledWith("Card missing image_id:", mockCardInvalid);

    consoleErrorSpy.mockRestore();
  });
});
