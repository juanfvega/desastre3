import './App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import UserFormContainer from './containers/App/UserFormContainer.jsx'
import { PlayerProvider } from './containers/App/PlayerContext.jsx'
import CreateGamePublic from './containers/App/CreateGamePublic.jsx'
import CreateLobby from './containers/App/CreateLobby.jsx'
import CreateListGames from './containers/App/CreateListGames.jsx'
import InGame from './containers/App/InGame.jsx'
import InGameTest from './containers/App/InGameTest.jsx'
import { WebSocketProvider } from "./containers/App/WebSocketContext.jsx"
import HomePage from './containers/App/HomePage.jsx'

function App() {

  return (
    <PlayerProvider>
    <WebSocketProvider> 
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />}/>
          <Route path="/create" element={< UserFormContainer />} />
            <Route path="/games/public" element={< CreateGamePublic />} />
            <Route path="/games/public/lobby/:game_id" element={< CreateLobby />} />
            <Route path="/games/public/in-game" element={< InGame />}/>
            <Route path="/games/public/in-game-test" element={< InGameTest />}/>
            <Route path="/games" element={< CreateListGames />}/>
            {/* 🎮 Rutas de desarrollo rápido - sin necesidad de backend */}
            <Route path="/dev/in-game" element={< InGame />}/>
            <Route path="/dev/test" element={< InGameTest />}/>
        </Routes>
      </Router>
    </WebSocketProvider>
    </PlayerProvider>
  )
}

export default App