import React from 'react';
import { useState } from 'react';
import { usePlayer } from './PlayerContext';
import { useNavigate } from 'react-router-dom';
import {createHttpService} from '../../services/HttpService';
import { useEffect } from 'react';
import Button from '../../components/Button';
 




 const fetchGames = async (setGames) => {
    const httpService = createHttpService();
        try {
            const data = await httpService.getGames();
            setGames(data);

        }catch(error) {
            console.error(error);
            setGames([]);
        }
 
};

export default function CreateListGames() {
    const [games, setGames] = useState([]);
    const navigate = useNavigate();
    const [refresh, setRefresh] = useState(0);
    const httpService = createHttpService();
    //player context 
    const { player } = usePlayer(); // jugador actual


    useEffect(() => {
        fetchGames(setGames);
      }, []); // llamar una vez

    useEffect(() => {
      }, [player]);


    useEffect(() => {
        fetchGames(setGames);
      }, [refresh]); // llamar cada vez que hace click en btn actualizar 

    // redirigir al lobby de la partida seleccionada
    const handleSelect = (game) => {
        if (!player || !player.player_id) {
        console.log("Esperando jugador...");
        return;
    }


        // llamada POST al backend para regristar ingreso al lobby
        // se espera que el backend envie confirmacion de ws join
        console.log("players en list games es:" , player.player_id)
        httpService.joinGame(game.id, player.player_id);
        navigate(`/games/public/lobby/${game.id}`);
        
    };

    const handleClick = () => {
        setRefresh(prev => prev + 1);

    };
 
    // volver al inicio
    const handleBack = () => {
        navigate(`/create`); // volver al inicio de crear user
    };

    return (
        
        <div>
            { (Array.isArray(games) && games.length > 0) ? (
                <div>
                <ul  className='list-group'>
                {games.map((game) => (
                    <li key={game.id} className= "list-group-item d-flex align-items-center"
                    >
                        <button 
                            type="button"
                            className={`"col-name list-group-item list-group-item-action" ${
                                    game.status !== 'waiting'
                                    ? "list-group-item list-group-item-action disabled"  // cuando la partida esta llena descativo el btn
                                    : "list-group-item list-group-item-action" // color cuando hay espacio, btn normal
                                }`}
                            onClick={() => handleSelect(game)} // call handleSelect
                            >
                                {game.nameGame}
                        </button>
                
                        <span className="badge-custom rounded-pill col-fixed">{game.num_players}</span>
                        <span
                                className={`badge-status rounded-pill col-fixed ${
                                    game.status !== 'waiting'// si la partida esta llena cambiar estado 
                                    ? "badge-full"   // color cuando la partida está llena
                                    : "badge-available" // color cuando hay espacio
                                }`}
                        >
                        </span>
                    </li>
                ))}
                </ul>
 

                <div className='container-list-btn'>
                    <Button text={"Actualizar"} className='btn-list-refresh' onClick={handleClick} />
                    <Button text={"Volver"}className='btn-list-back' onClick={handleBack} />
                </div>
 
            </div>
            ) : (
                <h1 data-testid="empty-heading" className='list-h1'>No hay partidas creadas</h1>
 
            )}
        </div>
        
    );
}

