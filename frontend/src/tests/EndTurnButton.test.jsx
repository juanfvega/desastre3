import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import EndTurnButton from '../components/EndTurnButton';

describe('EndTurnButton', () => {
  // Verifica que el botón está habilitado solo si todos los flags y handCompleted son true
  it('habilita el botón solo si todos los flags y handCompleted son true', () => {
    render(
      <EndTurnButton
        handCompleted={true}
        setCurrentTurn={() => {}}
        currentPlayerPlayEvent={true}
        currentPlayerPlaySet={true}
        currentPlayerAddOneDetectiveCard={true}
        playerId={'player1'}
        gameId={'game1'}
        isMyTurn={true}
        className="test-class"
      />
    );
    const button = screen.getByText('Terminar turno');
    expect(button.className).not.toContain('disabled');
  });

  // Verifica que el botón está deshabilitado si alguno de los flags o handCompleted es false
  it('deshabilita el botón si algún flag o handCompleted es false', () => {
    render(
      <EndTurnButton
        handCompleted={true}
        setCurrentTurn={() => {}}
        currentPlayerPlayEvent={false}
        currentPlayerPlaySet={true}
        currentPlayerAddOneDetectiveCard={true}
        playerId={'player1'}
        gameId={'game1'}
        isMyTurn={true}
        className="test-class"
      />
    );
    const button = screen.getByText('Terminar turno');
    expect(button.className).toContain('disabled');
  });
  // Verifica que cuando handCompleted es false, el botón está deshabilitado y no ejecuta la acción al hacer clic
  it('no permite hacer clic si handCompleted es false', async () => {
    const setCurrentTurnMock = vi.fn();
    render(
      <EndTurnButton
        handCompleted={false}
        setCurrentTurn={setCurrentTurnMock}
        currentPlayerPlayEvent={true}
        currentPlayerPlaySet={false}
        currentPlayerAddOneDetectiveCard={false}
        playerId={'player1'}
        gameId={'game1'}
        isMyTurn={true}
        className="test-class"
      />
    );
    const button = screen.getByText('Terminar turno');
    expect(button.className).toContain('disabled');
    await act(async () => {
      fireEvent.click(button);
    });
    // No debería llamar a setCurrentTurn porque el turno no termina
    expect(setCurrentTurnMock).not.toHaveBeenCalled();
  });
  // Verifica que al recibir el evento 'turn_ended' por WebSocket se actualiza el turno y se habilita el botón
  it('actualiza el turno y habilita el botón al recibir evento turn_ended', () => {
    // Mock para setCurrentTurn y wsService
    const setCurrentTurnMock = vi.fn();
    const wsServiceMock = {
      connect: vi.fn(),
      disconnect: vi.fn(),
      on: vi.fn(),
    };
    // Mock de useRef para wsService
    vi.spyOn(React, 'useRef').mockReturnValue({ current: wsServiceMock });
    render(
      <EndTurnButton
        handCompleted={true}
        setCurrentTurn={setCurrentTurnMock}
        currentPlayerPlayEvent={true}
        currentPlayerPlaySet={false}
        currentPlayerAddOneDetectiveCard={false}
        playerId={'player1'}
        gameId={'game1'}
        isMyTurn={true}
        className="test-class"
      />
    );
    // Simula el callback registrado en wsService.on
    const eventHandler = wsServiceMock.on.mock.calls[0][1];
    eventHandler({ event: 'turn_ended', game_id: 'game1', next_player: 'player2' });
    expect(setCurrentTurnMock).toHaveBeenCalledWith('player2');
  });
  
  // Verifica que el botón se renderiza si isMyTurn es true y handCompleted es true
  it('renderiza el botón si es mi turno y tengo la mano completa', () => {
    render(
      <EndTurnButton
        handCompleted={true}
        setCurrentTurn={() => {}}
        currentPlayerPlayEvent={true}
        currentPlayerPlaySet={false}
        currentPlayerAddOneDetectiveCard={false}
        playerId={'player1'}
        gameId={'game1'}
        isMyTurn={true}
        className="test-class"
      />
    );
    expect(screen.getByText('Terminar turno')).toBeInTheDocument();
  });

  // Verifica que el botón NO se renderiza si isMyTurn es false aunque tenga la mano completa
  it('no renderiza el botón si no es mi turno aunque tenga la mano completa', () => {
    render(
      <EndTurnButton
        handCompleted={true}
        setCurrentTurn={() => {}}
        currentPlayerPlayEvent={true}
        currentPlayerPlaySet={false}
        currentPlayerAddOneDetectiveCard={false}
        playerId={'player1'}
        gameId={'game1'}
        isMyTurn={false}
        className="test-class"
      />
    );
    expect(screen.queryByText('Terminar turno')).toBeNull();
  });


  // Verifica que el botón está deshabilitado si no se cumplen las condiciones y handCompleted es true
  it('deshabilita el botón si no se cumplen las condiciones y tengo la mano completa', () => {
    render(
      <EndTurnButton
        handCompleted={true}
        setCurrentTurn={() => {}}
        currentPlayerPlayEvent={false}
        currentPlayerPlaySet={false}
        currentPlayerAddOneDetectiveCard={false}
        playerId={'player1'}
        gameId={'game1'}
        isMyTurn={true}
        className="test-class"
      />
    );
    const button = screen.getByText('Terminar turno');
    expect(button.className).toContain('disabled');
  });
});
