import './GameScreen.css';

const GameScreen = ({ children }) => {
  return (
    <div className="game-screen">
      {children}
    </div>
  );
};

export default GameScreen;