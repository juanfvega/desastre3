import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import CardModal from "../components/CardModal";
/* 
Renderiza el CardModal abierto (isOpen=true) pero sin cartas.
Comprueba que se muestre el mensaje "No tienes cartas asignadas
*/
describe("CardModal", () => {
  it("muestra mensaje cuando no hay cartas", () => {
    const mockOnClose = vi.fn();

    render(
      <CardModal
        isOpen={true}
        onClose={mockOnClose}
        Cards={[]}   // Sin cartas
        onCardClick={vi.fn()}
      />
    );

    // Esperamos que se vea el mensaje de no hay cartas
    expect(screen.getByText(/No tienes cartas asignadas./i)).toBeInTheDocument();
  });

  /*
    Renderiza el CardModal cerrado (isOpen=false).
    Verifica que no se renderiza nada (container.firstChild es null).
 */

  it("no renderiza nada si isOpen es false", () => {
    const mockOnClose = vi.fn();

    const { container } = render(
      <CardModal
        isOpen={false}
        onClose={mockOnClose}
        Cards={[]}
        onCardClick={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });
});
