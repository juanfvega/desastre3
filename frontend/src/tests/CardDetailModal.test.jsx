// src/tests/CardDetailModal.test.jsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import CardDetailModal from "../components/CardDetailModal";

describe("CardDetailModal", () => {
  const mockCard = { name: "detective_Holmes", image_id: "detective_Holmes" };

  it("No renderiza nada si isOpen es false o card es null", () => {
    const { container } = render(<CardDetailModal isOpen={false} card={mockCard} />);
    expect(container.firstChild).toBeNull();

    const { container: container2 } = render(<CardDetailModal isOpen={true} card={null} />);
    expect(container2.firstChild).toBeNull();
  });

  it("Muestra la imagen de la carta cuando isOpen es true", () => {
    render(<CardDetailModal isOpen={true} card={mockCard} />);

    const img = screen.getByAltText(/Carta detective_Holmes/i);
    expect(img).toBeInTheDocument();
    expect(img.src).toContain("/Cards/detective_Holmes.png");
  });


  it("Retorna null si card.image_id y card.name son null", () => {
    const mockCard = { image_id: null, name: null };

    const { container } = render(
      <CardDetailModal
        isOpen={true}
        card={mockCard}
        onCardClick={() => {}}
        onUsedAction={() => {}}
        onDiscardAction={() => {}}
        onClose={() => {}}
      />
    );

    // container.firstChild debe ser null
    expect(container.firstChild).toBeNull();
  });

  it("Llama a las funciones onCardClick, onUsedAction y onDiscardAction al hacer click en los botones", () => {
    const onCardClick = vi.fn();
    const onUsedAction = vi.fn();
    const onDiscardAction = vi.fn();
    const onClose = vi.fn();

    render(
      <CardDetailModal
        isOpen={true}
        card={mockCard}
        onCardClick={onCardClick}
        onUsedAction={onUsedAction}
        onDiscardAction={onDiscardAction}
        onClose={onClose}
      />
    );

    // Botón "Usar" llama a onCardClick
    fireEvent.click(screen.getByText("Usar"));
    expect(onCardClick).toHaveBeenCalledWith(mockCard);

    // Botón "Descartar"
    fireEvent.click(screen.getByText("Descartar"));
    expect(onDiscardAction).toHaveBeenCalledWith(mockCard);

    // Click en overlay llama a onClose
    fireEvent.click(screen.getByText("Usar").closest(".card-detail-overlay"));
    expect(onClose).toHaveBeenCalled();
  });
});
