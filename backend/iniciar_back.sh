#!/bin/bash

# Carpeta donde está este script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Archivo requirements.txt (si no existe, lo crea)
REQ_FILE="$DIR/requirements.txt"
if [ ! -f "$REQ_FILE" ]; then
  cat > "$REQ_FILE" <<EOL
fastapi
uvicorn[standard]
pydantic
pytest
sqlalchemy
sqlmodel
databases
aiosqlite
httpx>=0.23
pytest
pytest-asyncio
websockets
EOL
fi

# Crear entorno virtual si no existe
if [ ! -d "$DIR/venv" ]; then
  python3 -m venv "$DIR/venv"
fi

# Abrir nueva terminal y ejecutar backend
gnome-terminal -- bash -c "cd \"$DIR\" && exec bash --rcfile <(echo 'source \"$DIR\"/venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload')"

