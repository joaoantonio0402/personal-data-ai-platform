from sqlalchemy import create_engine

from schema import Base


DATABASE_URL = (
    "postgresql://postgres:1234"
    "@localhost:5432/google_and_spotify"
)


engine = create_engine(
    DATABASE_URL
)


print("Creating tables...")

Base.metadata.create_all(engine)

print("Done!")