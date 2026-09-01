from sqlalchemy import create_engine

from src.database.schema import Base

def connect_to_database():
    DATABASE_URL = (
        "postgresql://postgres:1234"
        "@localhost:5432/google_and_spotify"
    )

    engine = create_engine(
        DATABASE_URL
    )
    return engine
