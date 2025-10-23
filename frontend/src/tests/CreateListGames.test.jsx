import React from 'react';
import { vi, test, expect } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react'; 
import * as HttpServiceModule from '../services/HttpService';

// ---------------- MOCKS ---------------- //

// Mock de PlayerContext
vi.mock('../containers/App/PlayerContext', () => ({
  usePlayer: () => ({
    player: { player_id: 1, name: 'TestPlayer' },
    updatePlayer: vi.fn(),
  }),
}));

// Mock de react-router-dom
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// ---------------- MOCK de HttpService antes de importar ---------------- //
const joinGameMock = vi.fn().mockResolvedValue({ success: true });

vi.mock("../services/HttpService", () => ({
  createHttpService: () => ({
    getGames: vi.fn().mockResolvedValue([
      { id: 1, nameGame: "P1", status: "waiting", owner: "owner" },
      { id: 2, nameGame: "P2", status: "full", owner: "owner" }
    ]),
    joinGame: joinGameMock,
  }),
}));

// ---------------- IMPORT COMPONENTE ---------------- //
import CreateListGames from '../containers/App/CreateListGames';

// ---------------- TESTS ---------------- //

test("renderiza partidas y activa/desactiva botones según status y click joinGame", async () => {
  await act(async () => {
    render(<CreateListGames />);
  });

  const btnP1 = await screen.findByRole("button", { name: "P1" });
  const btnP2 = await screen.findByRole("button", { name: "P2" });

  expect(btnP1).not.toHaveClass("disabled");
  expect(btnP2).toHaveClass("disabled");

  // click en partida activa
  await act(async () => {
    fireEvent.click(btnP1);
  });

  // ahora sí spy fue llamado con los parámetros correctos
  expect(joinGameMock).toHaveBeenCalledWith(1, 1); // gameId, playerId
});
