import React from 'react';
import Avatar from './Avatar';


const CardLobby = ({player}) => {
  return (
    <div className='card-item'>

        <Avatar src={'/src/assets/avatar1.png'}className={'avatar-lobby'}/>

        <h3 className='h3-lobby'>
            {player.name}
        </h3>
    </div>
  );
};


export default CardLobby;
