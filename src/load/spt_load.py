from pathlib import Path
import sys
import pandas as pd
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database

engine = connect_to_database()

with engine.connect() as conn:
    print("Conectado!")

    SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

project_root = Path(__file__).resolve().parents[2]

new_records_dir = (
        project_root
        / "data"
        / "processed"
        / "spotify"
    )

dim_artists_df = pd.read_csv(new_records_dir / "new_artists_enriched.csv")
dim_albums_df = pd.read_csv(new_records_dir / "new_albums_enriched.csv").drop("artist_name", axis=1)
dim_tracks_df = pd.read_csv(new_records_dir / "new_tracks_enriched.csv").drop("artist_name", axis=1)
fact_listening_df = pd.read_csv(new_records_dir / "new_streams.csv")




dim_artists_df.to_sql("dim_artist", con=engine, if_exists="append", index=False)
dim_albums_df.to_sql("dim_album", con=engine, if_exists="append", index=False)
dim_tracks_df.to_sql("dim_track", con=engine, if_exists="append", index=False)
fact_listening_df.to_sql("dim_track", con=engine, if_exists="append", index=False)