import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import ActionButton from "../components/ActionButton";

describe("ActionButton", () => {
  it("no renderiza nada si isVisible es false", () => {
    const { container } = render(<ActionButton />);
    expect(container.firstChild).toBeNull();
  });


  it("renderiza el botón si isVisible es true", () => {
    render(<ActionButton isVisible={true} />);
    expect(screen.getByText("No ejecutar acción")).toBeInTheDocument();
  });

});

  it("ejecuta la función onNoAction al hacer click si no está deshabilitado", () => {
    const mockFn = vi.fn();
    render(<ActionButton isVisible={true} onNoAction={mockFn} />);
    
    const button = screen.getByText("No ejecutar acción");
    fireEvent.click(button);

    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it("no ejecuta la función si el botón está deshabilitado", () => {
    const mockFn = vi.fn();
    render(<ActionButton isVisible={true} onNoAction={mockFn} disabled={true} />);
    
    const button = screen.getByText("No ejecutar acción");
    fireEvent.click(button);

    expect(mockFn).not.toHaveBeenCalled();
  });

  it("aplica la clase 'action-button-disabled' cuando está deshabilitado", () => {
    render(<ActionButton isVisible={true} disabled={true} />);
    const button = screen.getByText("No ejecutar acción");
    expect(button).toHaveClass("action-button-disabled");
  });

