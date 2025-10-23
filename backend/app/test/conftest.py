import pytest
import asyncio
from sqlalchemy import text
from app.core.database import database

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Elimina los datos de prueba creados por los tests al finalizar."""
    # Nos conectamos antes de los tests
    asyncio.run(database.connect())
    yield  # 👉 acá se ejecutan todos los tests
    # Luego del yield, hacemos la limpieza
    try:
        asyncio.run(database.execute(text("DELETE FROM players WHERE username = 'pepe_test';")))
        asyncio.run(database.execute(text("DELETE FROM games WHERE nameGame = 'PartidaTest';")))
    except Exception as e:
        print(f"Error al limpiar test data: {e}")
    finally:
        asyncio.run(database.disconnect())
