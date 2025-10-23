import React from 'react';
import { vi } from 'vitest';
import { test,expect } from 'vitest';
import {render, screen, fireEvent} from '@testing-library/react'; 
import CreateGamePublic from '../containers/App/CreateGamePublic';
import { act } from "@testing-library/react";

// Mock del fetch global
beforeEach(() => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ message: 'Mocked response' }),
    })
  );
});




vi.mock('../containers/App/PlayerContext', () => ({
    usePlayer: () => ({
        player: { player_id: 'mock-player-id' }, // ahora es un objeto
    
        updatePlayer: vi.fn(),
    }),
}));


vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'), // mantener los demás exports reales
  useNavigate: () => vi.fn(),             // mock de navigate
}));

/*Test muestra que los campos del formulario se llamen como debería llamarse*/
test("muestra campos con el texto correcto",()=> {
    act(() => {
        render(<CreateGamePublic />);
    }); 
    expect(screen.getByText("Nombre de Partida")).toBeInTheDocument();
    expect(screen.getByText("Nro de Jugadores")).toBeInTheDocument();
});

/*Test si el usuario no ingresa el nombre y se clickea el btn muestra el error*/
test("muestra mensaje de error si el nombre está vacío al crear partida",()=> {
    act(() => {
        render(<CreateGamePublic />);
    });
    const createButton = screen.getByText("Nueva Partida");

    act(() => {
        fireEvent.click(createButton);
    });

    expect(screen.getByText("El nombre de la partida es requerido")).toBeInTheDocument();
});

/*Test Ingreso datos al formulario correctos*/
test("formulario válido no muestra mensajes de error", async () => {
    act(() => {
            render(<CreateGamePublic />);
    });
  
  const nameGameInput = screen.getByPlaceholderText("Ingrese el nombre de la partida");
  const numberOfPlayers = screen.getByPlaceholderText("Ingrese nro de jugadores");
  const createButton = screen.getByText("Nueva Partida");

    await act(async () => {
    fireEvent.change(nameGameInput, { target: { value: "Partida 1" } });
    fireEvent.change(numberOfPlayers, { target: { value: "2" } });
    fireEvent.click(createButton);

    // si el clic dispara promesas, las esperamos
    await Promise.resolve(); // fuerza que se resuelvan microtasks
  });

  expect(nameGameInput.value).toBe("Partida 1");
  expect(numberOfPlayers.value).toBe("2");
});
