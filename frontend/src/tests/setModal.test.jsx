import React from 'react';
import { render, screen } from '@testing-library/react';
import SetsModal from '../containers/App/SetModal';

const mockSetsByPlayer = {
  'Jugador1': [
    { cards: [{ name: 'detective_quin' }, { name: 'detective_quin' }] },
    { cards: [{ name: 'detective_poirot' }, { name: 'detective_poirot' }, { name: 'detective_poirot' }] }
  ],
  'Jugador2': [
    { cards: [{ name: 'detective_marple' }, { name: 'detective_marple' }, { name: 'detective_marple' }] },
    { cards: [{ name: 'detective_oliver' }, { name: 'detective_oliver' }, { name: 'detective_oliver' }] }
  ]
};

describe('SetsModal', () => {
  it('renders modal with player names and sets', () => {
    render(
      <SetsModal
        isOpen={true}
        onClose={() => {}}
        gameId={"test-game"}
        playerId={"Jugador1"}
      />
    );
    expect(screen.getByText('Sets jugados')).toBeInTheDocument();
    expect(screen.getByText('Jugador1')).toBeInTheDocument();
    expect(screen.getByText('Jugador2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cerrar/i })).toBeInTheDocument();
  });
  it('no renderiza nada si isOpen es false', () => {
    const { container } = render(
      <SetsModal
        isOpen={false}
        onClose={() => {}}
        gameId={"test-game"}
        playerId={"Jugador1"}
      />
    );
    expect(container.firstChild).toBeNull();
  });
});
