import React from 'react';
import { useNavigate } from 'react-router-dom';
// import DevNavigation from '../../components/DevNavigation';

export default function HomePage() {
  const navigate = useNavigate();

  const handleClick = (e) => {
    e.preventDefault();
    navigate('/create');
  }

  return (
    <div className="home-container" onClick={handleClick}>
        {/* <DevNavigation /> */}
        <div className='home-container-image'>
        <img src="src/assets/titulo.png" alt="Imagen" className="home-image" />
        </div>
        <video
        src="src/assets/video_sin_audio.mp4"
        className="home-video"
        autoPlay
        muted
        />
        <h2 className='honk'>Press Start</h2>
    </div>
  );
}
