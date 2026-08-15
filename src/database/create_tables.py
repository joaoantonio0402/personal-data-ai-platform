from src.database.connection import connect_to_database

from src.database.schema import Base

print("Creating tables...")

Base.metadata.create_all(connect_to_database())

print("Done!")