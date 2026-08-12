import pandas as pd
from pathlib import Path
import datetime
from sqlalchemy import create_engine

def transform():

    BASE_DIR = Path(__file__).resolve().parent.parent

    csv_path = BASE_DIR / "listening_history.csv"

    df = pd.read_csv(csv_path)

    # =========================
    # ARTISTS
    # =========================

    artists_df = (
        df[["artist"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    artists_df["artist_id"] = range(1, len(artists_df) + 1)

    # adiciona artist_id ao dataframe principal
    df = df.merge(artists_df, on="artist")

    # =========================
    # ALBUMS
    # =========================

    albums_df = (
        df[["album", "artist_id"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    albums_df["album_id"] = range(1, len(albums_df) + 1)

    # adiciona album_id ao dataframe principal
    df = df.merge(
        albums_df,
        on=["album", "artist_id"]
    )

    # =========================
    # TRACKS
    # =========================

    tracks_df = (
        df[["track", "album_id"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    tracks_df["track_id"] = range(1, len(tracks_df) + 1)

    # adiciona track_id ao dataframe principal
    df = df.merge(
        tracks_df,
        on=["track", "album_id"]
    )

    # =========================
    # HISTORY
    # =========================

    history_df = df[["utc_time", "track_id"]]

    # =========================
    # EXPORT CSVs
    # =========================

    artists_df.to_csv("artists.csv", index=False)
    albums_df.to_csv("albums.csv", index=False)
    tracks_df.to_csv("tracks.csv", index=False)
    history_df.to_csv("history.csv", index=False)

def transform_from_date():

    BASE_DIR = Path(__file__).resolve().parent.parent

    csv_path = BASE_DIR / "listening_history.csv"

    df = pd.read_csv(csv_path)
    df["utc_time"] = pd.to_datetime(df["utc_time"])

    engine = create_engine(
    "mssql+pyodbc://DESKTOP-AKTMQH7\\SQLEXPRESS/Spotify?"
    "driver=ODBC+Driver+17+for+SQL+Server&"
    "trusted_connection=yes"
    )

    conn = engine.connect()
    print(conn)
    
    query = "SELECT MAX(utc_time) AS latest_date FROM history"

    latest = pd.read_sql(query, engine)

    latest_date = latest.iloc[0]["latest_date"]

    df = df[df["utc_time"] > latest_date]

     # =========================
    # ARTISTS
    # =========================

    artists_df = (
        df[["artist"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    artists_df["artist_id"] = range(1, len(artists_df) + 1)

    # adiciona artist_id ao dataframe principal
    df = df.merge(artists_df, on="artist")

    # =========================
    # ALBUMS
    # =========================

    albums_df = (
        df[["album", "artist_id"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    albums_df["album_id"] = range(1, len(albums_df) + 1)

    # adiciona album_id ao dataframe principal
    df = df.merge(
        albums_df,
        on=["album", "artist_id"]
    )

    # =========================
    # TRACKS
    # =========================

    tracks_df = (
        df[["track", "album_id"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    tracks_df["track_id"] = range(1, len(tracks_df) + 1)

    # adiciona track_id ao dataframe principal
    df = df.merge(
        tracks_df,
        on=["track", "album_id"]
    )

    # =========================
    # HISTORY
    # =========================

    history_df = df[["utc_time", "track_id"]]

    # =========================
    # EXPORT CSVs
    # =========================

    artists_db = pd.read_sql(
       "SELECT * FROM artists",
        engine
    )

    artists_df = artists_df[
        ~artists_df["artist_name"].isin(
            artists_db["artist_name"]
        )
    ]

    next_id = artists_db["artist_id"].max() + 1

    artists_df.to_csv("artists.csv", index=False)
    albums_df.to_csv("albums.csv", index=False)
    tracks_df.to_csv("tracks.csv", index=False)
    history_df.to_csv("history.csv", index=False)
    
    
transform_from_date()