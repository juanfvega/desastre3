import React from 'react';
import { test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { act } from '@testing-library/react';
import UserFormContainer from '../containers/App/UserFormContainer.jsx';

vi.mock('../containers/App/PlayerContext', () => ({
  usePlayer: () => ({
    player: 'mock-player',
    updatePlayer: vi.fn(),
  }),
}));

vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: () => vi.fn(),
}));

// 👇 Mock global del fetch
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ id: 1, player: 'mock-player' }),
  })
);

test("muestra campos con el texto correcto", () => {
  render(<UserFormContainer />);
  expect(screen.getByText("Usuario")).toBeInTheDocument();
  expect(screen.getByText("Fecha de nacimiento")).toBeInTheDocument();
  expect(screen.getByText("Crear Partida")).toBeInTheDocument();
  expect(screen.getByText("Unirse")).toBeInTheDocument();
});

test("muestra mensaje de error si el nombre está vacío al crear partida", () => {
  render(<UserFormContainer />);
  const createButton = screen.getByText("Crear Partida");
  fireEvent.click(createButton);
  expect(screen.getByText("El nombre de jugador es requerido")).toBeInTheDocument();
});

test("formulario válido no muestra mensajes de error", () => {
  render(<UserFormContainer />);
  const nameInput = screen.getByPlaceholderText("Ingrese su usuario");
  const birthdayInput = screen.getByPlaceholderText("Ingrese la fecha");
  const createButton = screen.getByText("Crear Partida");

  act(() => {
    fireEvent.change(nameInput, { target: { value: "Juan" } });
  });

  act(() => {
    fireEvent.change(birthdayInput, { target: { value: "1990-01-01" } });
  });

  act(() => {
    fireEvent.click(createButton);
  });

  expect(nameInput.value).toBe("Juan");
  expect(birthdayInput.value).toBe("1990-01-01");
});
