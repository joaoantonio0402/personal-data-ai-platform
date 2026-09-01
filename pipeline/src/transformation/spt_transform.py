import requests
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone

def parse_track(track):

    artist = track.get("artist", {})
    album = track.get("album", {})
    date = track.get("date", {})
    return {
        "track_mbid": track.get("mbid") or None,
        "track_name": track.get("name"),
        "artist_mbid": artist.get("mbid") or None,
        "artist_name": artist.get("#text"),
        "album_mbid": album.get("mbid") or None,
        "album_name": album.get("#text"),
        "timestamp_uts": int(date["uts"]) if date.get("uts") else None,
        "timestamp_utc": (
            datetime.fromtimestamp(int(date["uts"]), tz=timezone.utc)
            if date.get("uts") is not None
            else None
        ),
        "track_url": track.get("url"),
        "streamable": track.get("streamable"),
    }

def transform_data_from_raw_json(run_id = None):

    if run_id is None:
        print("Nenhum ID fornecido.")
        return
    else:
        raw_dir = Path(f"pipeline/data/raw/spotify/{run_id}/pages")

    rows = []
    
    for file in sorted(raw_dir.glob("*.json")):

        #print(f"Processando {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        tracks = data["recenttracks"]["track"]

        for track in tracks:
            rows.append(parse_track(track))

    df = pd.DataFrame(rows)

    df.to_csv(f"pipeline/data/processed/spotify/new_streams.csv", index=False)

    return df

    dim_artist_df = (
        df[
            ["artist_mbid", "artist_name"]
        ]
        .drop_duplicates(subset="artist_name")
        .copy()
    )

    dim_artist_last_saved = (
        pd.read_csv("pipeline/data/processed/spotify/dim_artist.csv")
        if Path("pipeline/data/processed/spotify/dim_artist.csv").exists() else pd.DataFrame(columns=["artist_mbid", "artist_name"])
    )

    new_artists = dim_artist_df[
        ~dim_artist_df["artist_name"].isin(
            dim_artist_last_saved["artist_name"]
        )
    ].copy()

    dim_artist_last_saved = pd.concat(
        [dim_artist_last_saved, new_artists],
        ignore_index=True
    )

    new_artists.to_csv(f"pipeline/data/processed/spotify/new_artists.csv", index=False)
    dim_artist_df.to_csv(f"pipeline/data/processed/spotify/dim_artist.csv", index=False)




    dim_album_df = (
        df[
            ["album_mbid", "album_name", "artist_name"]
        ]
        .drop_duplicates(subset=["album_name", "artist_name"])
        .copy()
    )

    dim_album_last_saved = (
        pd.read_csv("pipeline/data/processed/spotify/dim_album.csv")
        if Path("pipeline/data/processed/spotify/dim_album.csv").exists() else pd.DataFrame(columns=["album_mbid", "album_name"])
    )

    new_albums = dim_album_df[
        ~dim_album_df["album_name"].isin(
            dim_album_last_saved["album_name"]
        )
    ].copy()

    dim_album_df = pd.concat(
        [dim_album_last_saved, new_albums],
        ignore_index=True
    )

    new_albums.to_csv(f"pipeline/data/processed/spotify/new_albums.csv", index=False)
    dim_album_df.to_csv(f"pipeline/data/processed/spotify/dim_album.csv", index=False)




    dim_tracks_df = (
        df[
            ["track_mbid", "track_name", "artist_name"]
        ]
        .drop_duplicates(subset=["track_name", "artist_name"])
        .copy()
    )

    dim_tracks_last_saved = (
        pd.read_csv("pipeline/data/processed/spotify/dim_tracks.csv")
        if Path("pipeline/data/processed/spotify/dim_tracks.csv").exists() else pd.DataFrame(columns=["track_mbid", "track_name"])
    )

    new_tracks = dim_tracks_df[
        ~dim_tracks_df["track_name"].isin(
            dim_tracks_last_saved["track_name"]
        )
    ].copy()

    dim_tracks_df = pd.concat(
        [dim_tracks_last_saved, new_tracks],
        ignore_index=True
    )

    new_tracks.to_csv(f"pipeline/data/processed/spotify/new_tracks.csv", index=False)
    dim_tracks_df.to_csv(f"pipeline/data/processed/spotify/dim_tracks.csv", index=False)



# transform_data_from_raw_json(run_id = "")