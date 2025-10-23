import React, { createContext, useContext, useState } from "react";

const PlayerContext = createContext();

export function PlayerProvider({ children }) {
  const [player, setPlayer] = useState(null);

  // mergea el nuevo objeto con el anterior
  const updatePlayer = (newData) => {
    setPlayer((prev) => ({
      ...prev,
      ...newData,
    }));
  };

  return (
    <PlayerContext.Provider value={{ player, updatePlayer }}>
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  return useContext(PlayerContext);
}
