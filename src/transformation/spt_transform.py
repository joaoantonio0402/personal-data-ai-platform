import requests
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone

def create_artist_key(artist_name):
    if pd.isna(artist_name):
        return None
    return str(artist_name).strip().casefold()

def create_album_key(album_name, artist_name):
    if pd.isna(album_name) or pd.isna(artist_name):
        return None

    return (
        f"{str(album_name).strip().casefold()}"
        f"||"
        f"{str(artist_name).strip().casefold()}"
    )

def create_track_key(track_name, artist_name):
    if pd.isna(track_name) or pd.isna(artist_name):
        return None

    return (
        f"{str(track_name).strip().casefold()}"
        f"||"
        f"{str(artist_name).strip().casefold()}"
    )

def parse_track(track):

    artist = track.get("artist", {})
    album = track.get("album", {})
    date = track.get("date", {})

    track_name = track.get("name")
    artist_name = artist.get("#text")

    return {
        "track_mbid": track.get("mbid") or None,
        "track_name": track_name,
        "artist_mbid": artist.get("mbid") or None,
        "artist_name": artist_name,
        "album_mbid": album.get("mbid") or None,
        "album_name": album.get("#text"),
        "timestamp_uts": int(date["uts"]) if date.get("uts") else None,
        "timestamp_utc": (
            datetime.fromtimestamp(
                int(date["uts"]),
                tz=timezone.utc
            )
            if date.get("uts") is not None
            else None
        ),
        "track_url": track.get("url"),
        "streamable": track.get("streamable"),
        "artist_key": create_artist_key(artist_name),
        "album_key": create_album_key(
            album.get("#text"),
            artist_name
        ),
        "track_key": create_track_key(
            track_name,
            artist_name
        ),
    }

def transform_data_from_raw_json(id = None):

    if id is None:
        print("Nenhum ID fornecido.")
        return
    else:
        project_root = Path(__file__).resolve().parents[2]
        raw_dir = project_root / "data" / "raw" / "spotify" / str(id) / "pages"
        processed_dir = project_root / "data" / "processed" / "spotify"

    rows = []
    
    for file in sorted(raw_dir.glob("*.json")):

        #print(f"Processando {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        tracks = data["recenttracks"]["track"]

        for track in tracks:
            rows.append(parse_track(track))

    df = pd.DataFrame(rows)
    df.to_csv(processed_dir / "new_streams.csv", index=False)

    new_artists = (
        df[
            ["artist_mbid", "artist_name", "artist_key"]
        ]
        .drop_duplicates(subset="artist_name")
        .copy()
    )

    # dim_artist_last_saved = (
    #     pd.read_csv("data/processed/spotify/dim_artist.csv")
    #     if Path("data/processed/spotify/dim_artist.csv").exists() else pd.DataFrame(columns=["artist_mbid", "artist_name"])
    # )

    # new_artists = dim_artist_df[
    #     ~dim_artist_df["artist_name"].isin(
    #         dim_artist_last_saved["artist_name"]
    #     )
    # ].copy()

    # dim_artist_last_saved = pd.concat(
    #     [dim_artist_last_saved, new_artists],
    #     ignore_index=True
    # )

    new_artists.to_csv(processed_dir / "new_artists.csv", index=False)
    # dim_artist_df.to_csv(f"data/processed/spotify/dim_artist.csv", index=False)




    new_albums = (
        df[
            ["album_mbid", "album_name", "artist_name", "album_key"]
        ]
        .drop_duplicates(subset=["album_name", "artist_name"])
        .copy()
    )

    # dim_album_last_saved = (
    #     pd.read_csv("data/processed/spotify/dim_album.csv")
    #     if Path("data/processed/spotify/dim_album.csv").exists() else pd.DataFrame(columns=["album_mbid", "album_name"])
    # )

    # new_albums = dim_album_df[
    #     ~dim_album_df["album_name"].isin(
    #         dim_album_last_saved["album_name"]
    #     )
    # ].copy()

    # dim_album_df = pd.concat(
    #     [dim_album_last_saved, new_albums],
    #     ignore_index=True
    # )

    new_albums.to_csv(processed_dir / "new_albums.csv", index=False)
    #dim_album_df.to_csv(f"data/processed/spotify/dim_album.csv", index=False)




    new_tracks = (
        df[
            ["track_mbid", "track_name", "artist_name", "track_key"]
        ]
        .drop_duplicates(subset=["track_name", "artist_name"])
        .copy()
    )

    # dim_tracks_last_saved = (
    #     pd.read_csv("data/processed/spotify/dim_tracks.csv")
    #     if Path("data/processed/spotify/dim_tracks.csv").exists() else pd.DataFrame(columns=["track_mbid", "track_name"])
    # )

    # new_tracks = dim_tracks_df[
    #     ~dim_tracks_df["track_name"].isin(
    #         dim_tracks_last_saved["track_name"]
    #     )
    # ].copy()

    # dim_tracks_df = pd.concat(
    #     [dim_tracks_last_saved, new_tracks],
    #     ignore_index=True
    # )

    new_tracks.to_csv(processed_dir / "new_tracks.csv", index=False)
    return df
    #dim_tracks_df.to_csv(f"data/processed/spotify/dim_tracks.csv", index=False)