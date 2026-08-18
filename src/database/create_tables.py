import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database

from src.database.schema import Base

print("Creating tables...")

engine = connect_to_database()

Base.metadata.create_all(engine)

print("Done!")