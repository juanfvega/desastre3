import React, { useState, useEffect } from 'react';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Avatar from '../../components/Avatar';
import { createHttpService } from '../../services/HttpService';
import { usePlayer } from './PlayerContext';
import { useNavigate } from 'react-router-dom';

export default function UserFormContainer() {
  const [name, setName] = useState("");
  const [birthday, setBirthday] = useState("");
  const navigate = useNavigate();
  const [httpService] = useState(() => createHttpService());
  const [errors, setErrors] = useState({});
  const { player, updatePlayer } = usePlayer();

  const validateForm = () => {
    const newErrors = {};
    if (name.trim() === "") newErrors.name = "El nombre de jugador es requerido";
    if (birthday.trim() === "") newErrors.birthday = "La fecha de nacimiento es requerida";
  else if (!/^(0[1-9]|1[0-2])-\d{2}$/.test(birthday)) newErrors.birthday = "Formato debe ser MM-DD (mes 01-12)";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // manejar cambio de nombre
  const handleNameChange = (e) => setName(e.target.value);
  
  //  manejar cambio de cumpleaños
  const handleBirthdayChange = (e) => setBirthday(e.target.value);

  const handleClick = async (action) => {
    // validar formulario
    // valida el nombre y cumpleaños en formato MM-DD
    if (!validateForm()) return;

    const newPlayer = {
      username: name,
      birthdate: birthday,
      avatar: "/src/assets/avatar1.png"
    };

    try {
        // crea en backend
        const resp = await httpService.createPlayer(newPlayer);   // ← resp
        const fullPlayer = { ...newPlayer, player_id: resp.id };
      
        // actualiza contexto
        updatePlayer(fullPlayer);
      
        // guarda identidad y datos en *sessionStorage*
        sessionStorage.setItem("current_player_id", resp.id);     // ← usar resp
        sessionStorage.setItem("current_player", JSON.stringify(fullPlayer));
      
        // verificar leyendo del mismo lugar
        console.log("✅ current_player_id guardado:", sessionStorage.getItem("current_player_id"));
      
        // navega luego de guardar
        if (action === "create") navigate('/games/public');
        else if (action === "join") navigate('/games');
      
      } catch (error) {
        console.error('Error creating player:', error);
      }
  };

  useEffect(() => {}, [player]);

  return (
    <div className='frame-user-form'>
      <div className='inputfield'>
        <label className='label'>Usuario</label>
        <Input type='text' id='user' className='input' placeholder='Ingrese su usuario' onChange={handleNameChange} />
        {errors.name && <p className="error">{errors.name}</p>}
      </div>

      <div className='inputfield'>
        <label className='label'>Fecha de nacimiento</label>
        <Input type='text' id='date' className='input' placeholder='MM-DD' 
          maxLength={5} onChange={handleBirthdayChange} />
        {errors.birthday && <p className="error">{errors.birthday}</p>}
      </div>

      <div className='div-avatar'>
        <Avatar src="/src/assets/avatar1.png" size={100} />
      </div>

      <div className='buttons-usersform'>
        <Button text="Crear Partida" className="btn-user-form" onClick={() => handleClick("create")} />
        <Button text="Unirse" className="btn-user-form" onClick={() => handleClick("join")} />
      </div>
    </div>
  );
}
