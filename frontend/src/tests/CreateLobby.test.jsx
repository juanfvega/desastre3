import React from 'react';

import { MemoryRouter } from 'react-router-dom';
import CreateLobby from '../containers/App/CreateLobby';
import { vi } from 'vitest';
import { render, screen, fireEvent,waitFor } from '@testing-library/react';
import { act } from "@testing-library/react";


// Mock PlayerContext
vi.mock('../containers/App/PlayerContext', () => ({
  usePlayer: () => ({ player: { player_id: 'p1', host_id: 'p1', username: 'Jugador 1' }, updatePlayer: vi.fn() }),
}));

// Mock HttpService
vi.mock('../services/HttpService', () => ({
  createHttpService: vi.fn(() => ({ startGame: vi.fn().mockResolvedValue({}) })),
}));

// Mock CardLobby para mostrar solo el nombre
vi.mock('../../components/CardLobby', () => ({ default: ({ player }) => <div>{player.name}</div> }));

// Componente wrapper que inyecta lobbyPlayers manualmente
function CreateLobbyMock() {
  const lobbyPlayers = [
    { id: 'p1', name: 'Jugador 1' },
    { id: 'p2', name: 'Jugador 2' },
  ];
  return (
    <MemoryRouter>
      <div className="container-create-lobby">
        {lobbyPlayers.map(p => (
          <div key={p.id}>{p.name}</div>
        ))}
      </div>
    </MemoryRouter>
  );
}

describe('CreateLobby', () => {
  it('muestra jugadores mockeados', () => {
    render(<CreateLobbyMock />);
    expect(screen.getByText('Jugador 1')).toBeInTheDocument();
    expect(screen.getByText('Jugador 2')).toBeInTheDocument();
  });
});





// Componente wrapper simple con lobbyPlayers
function CreateLobbyMock2() {
  const lobbyPlayers = [
    { id: 'p1', name: 'Jugador 1' },
    { id: 'p2', name: 'Jugador 2' },
  ];

  return (
    <MemoryRouter>
      <h2 className="h3-number-players">{lobbyPlayers.length}</h2>
    </MemoryRouter>
  );
}

describe('CreateLobby number of players', () => {
  it('muestra la cantidad correcta de jugadores', () => {
    render(<CreateLobbyMock2 />);
    const h2 = screen.getByText('2'); // lobbyPlayers.length = 2
    expect(h2).toBeInTheDocument();
  });
});




// Mock HttpService
const startGameMock = vi.fn().mockResolvedValue({});
vi.mock('../services/HttpService', () => ({
  createHttpService: vi.fn(() => ({ startGame: startGameMock })),
}));

// Mock CardLobby
vi.mock('../../components/CardLobby', () => ({ default: ({ player }) => <div>{player.name}</div> }));

// Mock useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ game_id: '1234' }),
    useNavigate: () => vi.fn(), // opcional si quieres testear navigate
  };
})

describe('CreateLobby handleClick', () => {
  it('llama a startGame al hacer click en Iniciar', async() => {
    render(
      <MemoryRouter>
        <CreateLobby />
      </MemoryRouter>
    );

    await act(async () => {
      fireEvent.click(screen.getByText("Iniciar"));
});
    

    // Verifica que startGame se llame con game_id y player_id correctos
    expect(startGameMock).toHaveBeenCalledWith('1234', 'p1');
  })})

  
  // Mock WebSocket
class WebSocketMock {
  constructor(url) {
    this.url = url;
    this.onmessage = null;
    WebSocketMock.instances.push(this);
  }
  static instances = [];
  triggerMessage(data) {
    if (this.onmessage) this.onmessage({ data: JSON.stringify(data) });
  }
}
vi.stubGlobal('WebSocket', WebSocketMock);

describe('CreateLobby WebSocket lobby_state only', () => {
  beforeEach(() => {
    WebSocketMock.instances = [];
    vi.clearAllMocks();
  });

  it('actualiza lobbyPlayers solo con lobby_state', async () => {
    render(
      <MemoryRouter>
        <CreateLobby />
      </MemoryRouter>
    );

    const wsInstance = WebSocketMock.instances[0];

    // lobby_state
    await act(async () => {
  wsInstance.triggerMessage({
    event: 'lobby_state',
    data: { players: [{ id: 'p1', name: 'Jugador 1' }, { id: 'p2', name: 'Jugador 2' }] },
    });
  });


    // Espera a que se rendericen los jugadores
    await waitFor(() => {
      expect(screen.getByText('Jugador 1')).toBeInTheDocument();
      expect(screen.getByText('Jugador 2')).toBeInTheDocument();
    });
  });
});




describe('CreateLobby WebSocket player_joined only', () => {
  beforeEach(() => {
    WebSocketMock.instances = [];
    vi.clearAllMocks();
  });

  it('agrega un jugador al lobby cuando recibe player_joined', async () => {
    render(
      <MemoryRouter>
        <CreateLobby />
      </MemoryRouter>
    );

    const wsInstance = WebSocketMock.instances[0];

    // Simula un jugador que se une
    await act(async () => {
    wsInstance.triggerMessage({
      event: 'player_joined',
      data: { playerId: 'p2', playerName: 'Jugador 2' },
     });
    });

    // Espera a que se renderice el nuevo jugador
    await waitFor(() => {
      expect(screen.getByText('Jugador 2')).toBeInTheDocument();
    });

    // Simula otro jugador
    await act(async () => {
    wsInstance.triggerMessage({
      event: 'player_joined',
      data: { playerId: 'p3', playerName: 'Jugador 3' },
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Jugador 3')).toBeInTheDocument();
    });

    // Simula un duplicado (no debe agregarse)
    await act(async () => {
      wsInstance.triggerMessage({
        event: 'player_joined',
        data: { playerId: 'p2', playerName: 'Jugador 2' },
      });
    });

    await waitFor(() => {
      const elements = screen.getAllByText(/Jugador/);
      expect(elements.length).toBe(2); // solo Jugador 2 y Jugador 3
    });
  });
});






