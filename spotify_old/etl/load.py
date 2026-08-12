import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

def add_to_sql(data:pd.DataFrame, name:str):
    data.to_sql(
        name,
        engine,
        if_exists="replace",
        index=False
    )
    return

engine = create_engine(
    "mssql+pyodbc://DESKTOP-AKTMQH7\\SQLEXPRESS/Spotify?"
    "driver=ODBC+Driver+17+for+SQL+Server&"
    "trusted_connection=yes"
)

conn = engine.connect()

print(conn)

# SQL INSERT

BASE_DIR = Path(__file__).resolve().parent.parent

albuns = pd.read_csv(BASE_DIR / "albums.csv")
artists = pd.read_csv(BASE_DIR / "artists.csv")
tracks = pd.read_csv(BASE_DIR / "tracks.csv")
history = pd.read_csv(BASE_DIR / "history.csv")

add_to_sql(data=albuns, name="albuns")
add_to_sql(data=artists, name="artists")
add_to_sql(data=tracks, name="tracks")
add_to_sql(data=history, name="history")
