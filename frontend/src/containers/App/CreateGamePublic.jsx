import React, { useState } from 'react';
import Input from '../../components/Input';
import Button from '../../components/Button';
import { createHttpService } from '../../services/HttpService';     
import { usePlayer } from './PlayerContext';
import { useNavigate } from 'react-router-dom';

export default function CreateGamePublic() {
  const [name, setName] = useState('');
  const [numberOfPlayers, setNumberOfPlayers] = useState('');
  const [errors, setErrors] = useState({});
  const httpService = createHttpService();
  const { player, updatePlayer } = usePlayer();
  const navigate = useNavigate();

  // Validaciones mínimas
  const validateForm = () => {
    const newErrors = {};
    const trimmedName = name.trim();
    const numPlayers = Number(numberOfPlayers);

    if (!trimmedName) {
      newErrors.name = 'El nombre de la partida es requerido';
    }
    if (!Number.isFinite(numPlayers) || numPlayers < 2 || numPlayers > 6) {
      newErrors.numberOfPlayers = 'Número de jugadores inválido (2-6)';
    }
    if (!player?.player_id) {
      newErrors.player = 'No hay jugador activo (player_id no definido)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleClick = async () => {
    if (!validateForm()) return;

    const body = {
      nameGame: name.trim(),                
      num_players: Number(numberOfPlayers), 
      player_id: player.player_id,          
      password: null,                        
    };

    try {
      const game = await httpService.createGamePublic(body);

      // Actualizo player en contexto: me marco como host
      updatePlayer({
        ...player,
        player_id: player.player_id,
        host_id: player.player_id,
      });

      // Me uno a la partida recién creada
      try {
        await httpService.joinGame(game.id, player.player_id);
      } catch (e) {
        // si ya sos host y el back no requiere join explícito, podés ignorar
        console.warn('joinGame falló (posible no necesario para host):', e);
      }

      // Redirijo al lobby
      navigate(`/games/public/lobby/${game.id}`);
    } catch (err) {
      console.error('Error create game public:', err.status, err.endpoint, err.payload);
      const detail = err?.payload?.detail || 'Error al crear la partida';
      setErrors((prev) => ({ ...prev, submit: detail }));
      // opcional: alert(detail);
    }
  };

  return (
    <div className="frame-create-game">
      <div className="form-create-game">
        <div className="inputfield-create-game">
          <label className="label-create-game">Nombre de Partida</label>
          <Input
            type="text"
            id="game-name"
            className="input-create-game"
            placeholder="Ingrese el nombre de la partida"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          {errors.name && <p className="error-create-name">{errors.name}</p>}
        </div>

        <div className="inputfield-create-game">
          <label className="label-create-game">Nro de Jugadores</label>
          <Input
            type="number"
            id="players"
            className="input-create-game"
            placeholder="Ingrese nro de jugadores"
            value={numberOfPlayers}
            onChange={(e) => setNumberOfPlayers(e.target.value)}
            min={2}
            max={6}
          />
          {errors.numberOfPlayers && (
            <p className="error-create-name">{errors.numberOfPlayers}</p>
          )}
        </div>

        {errors.player && <p className="error-create-name">{errors.player}</p>}
        {errors.submit && <p className="error-create-name">{errors.submit}</p>}
      </div>

      <div className="buttons-create-game">
        <div>
          <Button
            text="Nueva Partida"
            className="btn-create-game"
            type="button"
            onClick={handleClick}
          />
        </div>
      </div>
    </div>
  );
}