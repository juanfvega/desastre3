from databases import Database
from sqlalchemy import create_engine, MetaData

# SQLite en app/db.sqlite3
DATABASE_URL = "sqlite:///./app/db.sqlite3"

# Base de datos asíncrona
database = Database(DATABASE_URL)

# Engine para crear tablas
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()