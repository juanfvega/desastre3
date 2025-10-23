from fastapi import FastAPI
from app.api.routes import players, games
from app.core.database import engine, metadata, database
from app.api.routes import websocket, players, games, websocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

origins = ["*"]

# Crear tablas para DataBase si no existen
metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conexión al inicio
    await database.connect()
    yield
    # Desconexión al finalizar
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Routers
app.include_router(players.router, prefix="/api", tags=["players"])
app.include_router(games.router, prefix="/api", tags=["games"])
app.include_router(websocket.router, tags=["websocket"])
    
@app.get("/")
async def root():
    return {"message": "Game API is running"}

if __name__ == "__main__":
    #import uvicorn #viejo
    #uvicorn.run(app, host="0.0.0.0", port=8000)
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )