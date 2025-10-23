  import React, { useEffect, useState, useRef } from "react";
  import Button from '../../components/Button';
  import { usePlayer } from './PlayerContext';
  import { useNavigate } from 'react-router-dom';
  import CardLobby from '../../components/CardLobby';
  import { useParams } from "react-router-dom";
  import { createHttpService } from '../../services/HttpService';

  


  export default function CreateLobby() {
    const { player, updatePlayer } = usePlayer();
    const navigate = useNavigate();
    const { game_id } = useParams(); // obtiene el id de la URL
    const [lobbyPlayers, setLobbyPlayers] = useState([]);
    const httpService = createHttpService();
    const lobbyRef = useRef(lobbyPlayers);



    // mantener la ref actualizada
    useEffect(() => {
      lobbyRef.current = lobbyPlayers;
    }, [lobbyPlayers]);

    useEffect(() => {
    // Verificar si player y game_id están disponibles
      
      if (!game_id) {
        console.warn('No game_id proporcionado');
        return;
      }

      if (!player?.player_id) {
        // Intentar restaurar player desde localStorage
        const storedPlayer = JSON.parse(localStorage.getItem('player'));
        if (storedPlayer) {
          console.log('Restaurando player desde localStorage:', storedPlayer);
          updatePlayer(storedPlayer);
        } else {
          console.warn('No hay datos de player...');
          return;
        }
      }
    });

    useEffect(() => {

      
      if(!game_id) return; // espero a que llegue 
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/games/${game_id}`);

      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        //console.log("mensaje de lobby state es", msg)
        switch (msg.event) {
          case "lobby_state":
            setLobbyPlayers(prev => {
            const newPlayers = msg.data.players;
            // si son iguales, no actualizar
            if (JSON.stringify(prev) === JSON.stringify(newPlayers)) return prev;
            return newPlayers;
          });
          break;

          case "player_joined":
            const newPlayer = {
              id: msg.data.playerId,
              name: msg.data.playerName,
            };
            //console.log("player_joined: msg in player joined", msg);
            setLobbyPlayers(prev => {
              // evitar duplicados
              if (prev.find(p => p.id === newPlayer.id)) return prev;
              return [...prev, newPlayer];
            });
            
            break;

          case "player_left":
            const leavingId = msg.data.playerId;
            setLobbyPlayers(prev => prev.filter(p => p.id !== leavingId));
            //console.log("Salió un jugador:", leavingId);
            break;

          case "game_starting":
            // debería mandar status a in game
            //console.log("mensaje en game starting",msg)
            const gameStatus = {
              "game_id": msg.game_id,
              "first_player": msg.first_player, // este es el primer que tiene el turno no el host
              "players_count": msg.players_count,
              "list_players": lobbyRef.current,
              "host_id": player.host_id
            }
            console.log("La partida comenzó nav to game...:", msg);
            // se reparten las cartas en el game
            navigate('/games/public/in-game', {state:gameStatus});
            break;
      
        }
  };
    }, [game_id]);


    const handleClick = () => {
      if(!player.player_id){
        console.warn("player no esta definido");
        return;
      }
      // esta el player?

        httpService.startGame(game_id, player.player_id)
        .then(response => {
          console.log("inicio partida:", response);
        })
        .catch(error => {
          console.error("Error create game public", error);
        });
      };


    return (
      
      <div>
        <div className="frame-create-lobby">
          <div className="container-create-lobby">
            {lobbyPlayers.map((p) => (
              <CardLobby key={p.id} player={p} />
            ))}
          </div>
          <div>
            {player.player_id === player.host_id && (
            <Button
              text="Iniciar"
              className="btn-create-lobby"
              type="submit"
              onClick={handleClick}
            />
            )}            
            <h2 className="h3-number-players">
              {lobbyPlayers.length}
            </h2>
          </div>
        </div>
      </div>
    );
  }