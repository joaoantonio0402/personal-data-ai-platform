import pandas as pd
from pathlib import Path
import pandas as pd
import sys
import os
from dotenv import load_dotenv
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.clients import spotify_client, melodata_client, reccobeats_client

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
MELODATA_API_KEY = os.getenv("MELODATA_API_KEY")

import logging
from pathlib import Path

import pandas as pd

from src.clients import spotify_client
from src.clients import melodata_client
from src.clients import reccobeats_client


logger = logging.getLogger(__name__)


def enrich_melodata(row):
    try:
        if pd.isna(row["spotify_isrc"]):
            logger.warning(
                f"Melodata skipped | "
                f"track={row['track_name']} | "
                f"artist={row['artist_name']} | "
                f"reason=missing ISRC"
            )
            return None

        logger.info(
            f"Melodata | "
            f"track={row['track_name']} | "
            f"artist={row['artist_name']}"
        )

        return melodata_client.get_track_features(
            MELODATA_API_KEY,
            row["spotify_isrc"]
        )

    except Exception as e:
        logger.error(
            f"Melodata failed | "
            f"track={row['track_name']} | "
            f"artist={row['artist_name']} | "
            f"isrc={row['spotify_isrc']} | "
            f"error={e}"
        )

        return None


def search_recco_track(row):
    try:
        logger.info(
            f"ReccoBeats search | "
            f"track={row['track_name']} | "
            f"artist={row['artist_name']}"
        )

        result = reccobeats_client.search_track(
            row["track_name"],
            row["artist_name"]
        )

        if not result:
            logger.warning(
                f"ReccoBeats returned no result | "
                f"track={row['track_name']} | "
                f"artist={row['artist_name']}"
            )
            return None

        return result

    except Exception as e:
        logger.error(
            f"ReccoBeats search failed | "
            f"track={row['track_name']} | "
            f"artist={row['artist_name']} | "
            f"error={e}"
        )

        return None


def get_recco_audio_features_safe(row):
    try:
        if pd.isna(row["recco_track_id"]):
            logger.warning(
                f"ReccoBeats features skipped | "
                f"track={row['track_name']} | "
                f"reason=missing ReccoBeats ID"
            )
            return None

        logger.info(
            f"ReccoBeats features | "
            f"track={row['track_name']} | "
            f"recco_id={row['recco_track_id']}"
        )

        return reccobeats_client.get_audio_features(
            row["recco_track_id"]
        )

    except Exception as e:
        logger.error(
            f"ReccoBeats features failed | "
            f"track={row['track_name']} | "
            f"recco_id={row['recco_track_id']} | "
            f"error={e}"
        )

        return None


def enrich_data():

    project_root = Path(__file__).resolve().parents[2]

    new_records_dir = (
        project_root
        / "data"
        / "processed"
        / "spotify"
    )

    logger.info("Starting enrichment pipeline")

    # ------------------------------------------------------------------
    # LOAD
    # ------------------------------------------------------------------

    try:

        df_new_streams = pd.read_csv(
            new_records_dir / "new_streams.csv"
        ).head(10)

        df_new_artists = pd.read_csv(
            new_records_dir / "new_artists.csv"
        ).head(10)

        df_new_albums = pd.read_csv(
            new_records_dir / "new_albums.csv"
        ).head(10)

        df_new_tracks = pd.read_csv(
            new_records_dir / "new_tracks.csv"
        ).head(10)

        logger.info(
            f"Input loaded | "
            f"artists={len(df_new_artists)} | "
            f"albums={len(df_new_albums)} | "
            f"tracks={len(df_new_tracks)}"
        )

    except Exception as e:

        logger.exception(
            f"Failed to load input data | error={e}"
        )

        return

    # ------------------------------------------------------------------
    # SPOTIFY
    # ------------------------------------------------------------------

    try:

        logger.info("Creating Spotify client")

        sp = spotify_client.create_spotify_client(
            CLIENT_ID,
            CLIENT_SECRET
        )

        logger.info("Spotify client created")

    except Exception as e:

        logger.exception(
            f"Failed to create Spotify client | error={e}"
        )

        return

    # ------------------------------------------------------------------
    # ARTISTS
    # ------------------------------------------------------------------

    logger.info("Starting artist enrichment")

    artist_results = []

    for _, row in df_new_artists.iterrows():

        try:

            logger.info(
                f"Spotify artist | "
                f"artist={row['artist_name']}"
            )

            result = spotify_client.get_artist_data(
                row["artist_name"],
                sp
            )

            artist_results.append(result)

        except Exception as e:

            logger.error(
                f"Spotify artist failed | "
                f"artist={row['artist_name']} | "
                f"error={e}"
            )

            artist_results.append(None)

    df_new_artists["spotify_data"] = artist_results

    artist_data_spotify = pd.json_normalize(
        df_new_artists["spotify_data"]
    )

    df_new_artists = pd.concat(
        [
            df_new_artists.drop(columns=["spotify_data"]),
            artist_data_spotify
        ],
        axis=1
    )

    logger.info("Artist enrichment completed")

    # ------------------------------------------------------------------
    # ALBUMS
    # ------------------------------------------------------------------

    logger.info("Starting album enrichment")

    album_results = []

    for _, row in df_new_albums.iterrows():

        try:

            logger.info(
                f"Spotify album | "
                f"album={row['album_name']} | "
                f"artist={row['artist_name']}"
            )

            result = spotify_client.get_album_data(
                row["album_name"],
                row["artist_name"],
                sp
            )

            album_results.append(result)

        except Exception as e:

            logger.error(
                f"Spotify album failed | "
                f"album={row['album_name']} | "
                f"artist={row['artist_name']} | "
                f"error={e}"
            )

            album_results.append(None)

    df_new_albums["spotify_data"] = album_results

    album_data_spotify = pd.json_normalize(
        df_new_albums["spotify_data"]
    )

    df_new_albums = pd.concat(
        [
            df_new_albums.drop(columns=["spotify_data"]),
            album_data_spotify
        ],
        axis=1
    )

    logger.info("Album enrichment completed")

    # ------------------------------------------------------------------
    # TRACKS - SPOTIFY
    # ------------------------------------------------------------------

    logger.info("Starting Spotify track enrichment")

    track_results = []

    for _, row in df_new_tracks.iterrows():

        try:

            logger.info(
                f"Spotify track | "
                f"track={row['track_name']} | "
                f"artist={row['artist_name']}"
            )

            result = spotify_client.get_track_data(
                row["track_name"],
                row["artist_name"],
                sp
            )

            track_results.append(result)

        except Exception as e:

            logger.error(
                f"Spotify track failed | "
                f"track={row['track_name']} | "
                f"artist={row['artist_name']} | "
                f"error={e}"
            )

            track_results.append(None)

    df_new_tracks["spotify_data"] = track_results

    track_data_spotify = pd.json_normalize(
        df_new_tracks["spotify_data"]
    )

    df_new_tracks = pd.concat(
        [
            df_new_tracks.drop(columns=["spotify_data"]),
            track_data_spotify
        ],
        axis=1
    )

    logger.info("Spotify track enrichment completed")

    # ------------------------------------------------------------------
    # MELODATA
    # ------------------------------------------------------------------

    logger.info("Starting Melodata enrichment")

    df_new_tracks["melodata_audio_features"] = df_new_tracks.apply(
        enrich_melodata,
        axis=1
    )

    logger.info("Melodata enrichment completed")

    # ------------------------------------------------------------------
    # RECCOBEATS - SEARCH
    # ------------------------------------------------------------------

    logger.info("Starting ReccoBeats track search")

    df_new_tracks["recco_search_result"] = df_new_tracks.apply(
        search_recco_track,
        axis=1
    )

    # Extract ReccoBeats ID
    def extract_recco_id(result):

        try:

            if not result:
                return None

            content = result.get("content", [])

            if not content:
                return None

            return content[0].get("id")

        except Exception:

            return None

    df_new_tracks["recco_track_id"] = (
        df_new_tracks["recco_search_result"]
        .apply(extract_recco_id)
    )

    logger.info("ReccoBeats search completed")

    # ------------------------------------------------------------------
    # RECCOBEATS - AUDIO FEATURES
    # ------------------------------------------------------------------

    logger.info(
        "Starting ReccoBeats audio features enrichment"
    )

    df_new_tracks["recco_audio_features"] = df_new_tracks.apply(
        get_recco_audio_features_safe,
        axis=1
    )

    logger.info(
        "ReccoBeats audio features enrichment completed"
    )

    # Remove intermediate search result
    df_new_tracks.drop(
        columns=["recco_search_result"],
        inplace=True
    )

    # ------------------------------------------------------------------
    # NORMALIZE FEATURES COLUMNS
    # ------------------------------------------------------------------

    logger.info("Normalizing audio features columns")

    # Normalize Melodata features
    melodata_features = pd.json_normalize(
        df_new_tracks["melodata_audio_features"]
    )
    melodata_features.columns = [
        f"melodata_{col}" for col in melodata_features.columns
    ]

    df_new_tracks = pd.concat(
        [
            df_new_tracks.drop(columns=["melodata_audio_features"]),
            melodata_features
        ],
        axis=1
    )

    # Normalize ReccoBeats features
    reccobeats_features = pd.json_normalize(
        df_new_tracks["recco_audio_features"]
    )
    reccobeats_features.columns = [
        f"reccobeats_{col}" for col in reccobeats_features.columns
    ]

    df_new_tracks = pd.concat(
        [
            df_new_tracks.drop(columns=["recco_audio_features"]),
            reccobeats_features
        ],
        axis=1
    )

    logger.info("Features columns normalized successfully")

    # ------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------

    try:

        logger.info("Saving enriched data")

        df_new_streams = df_new_streams[["timestamp_utc", "timestamp_uts", "track_url"]]

        df_new_streams.to_csv(
            new_records_dir / "new_streams_enriched.csv",
            index=False
        )        

        df_new_artists.to_csv(
            new_records_dir / "new_artists_enriched.csv",
            index=False
        )

        df_new_albums.to_csv(
            new_records_dir / "new_albums_enriched.csv",
            index=False
        )

        df_new_tracks.to_csv(
            new_records_dir / "new_tracks_enriched.csv",
            index=False
        )

        logger.info(
            "Enriched data saved successfully"
        )

    except Exception as e:

        logger.exception(
            f"Failed to save enriched data | error={e}"
        )

        return

    logger.info(
        "Enrichment pipeline completed successfully"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    enrich_data()






















#     sp = create_spotify_client(
#         CLIENT_ID,
#         CLIENT_SECRET
#     )

#     PROJECT_ROOT = Path(__file__).resolve().parents[2]

#     new_tracks_path = PROJECT_ROOT / "data" / "processed" / "spotify" / "new_tracks.csv"
#     new_tracks_enriched_path = PROJECT_ROOT / "data" / "processed" / "spotify" / "new_tracks_enriched.csv"

#     df = pd.read_csv(
#         new_tracks_path,
#         encoding="utf-8"
#     )

#     #df = df.head(10)

#     df = df[["track_name", "artist_name"]]

#     df = df.drop_duplicates(["track_name", "artist_name"])

#     # df["spotify_id"] = df.apply(
#     #     lambda row: get_track_id(row["track_name"], row["artist_name"], CLIENT_ID, CLIENT_SECRET), axis=1
#     # )



#     def get_artist_data(artist_name, client_id, client_secret):
#         sp = spotipy.Spotify(
#             auth_manager=SpotifyClientCredentials(
#                 client_id=client_id,
#                 client_secret=client_secret
#             )
#         )

#         query = f"artist:{artist_name}"

#         results = sp.search(
#             q=query,
#             type="artist",
#             limit=1
#         )

#         artists = results["artists"]["items"]

#         if not artists:
#             return None

#         artist = artists[0]

#         return {
#             "artist_id": artist["id"],
#             "artist_name": artist["name"],
#             "artist_url": artist["external_urls"].get("spotify"),
#             "followers": artist["followers"]["total"],
#             "popularity": artist["popularity"],
#             "genres": artist["genres"],
#             "artist_uri": artist["uri"]
#         }

        












#     df["isrc"] = df.apply(
#         lambda row: get_track_isrc(row["track_name"], row["artist_name"], CLIENT_ID, CLIENT_SECRET), axis=1
#     )

#     df.to_csv(new_tracks_enriched_path)
#     print("parte 1")

#     df["features"] = df.apply(
#         get_features_safe,
#         axis=1
#     )

#     df.to_csv(new_tracks_enriched_path)
#     print("parte 2")

#     df["recco_result"] = df.apply(
#         lambda row: search_recco_safe(row),
#         axis=1
#     )

#     df["recco_id"] = df["recco_result"].apply(
#         lambda x: x["content"][0]["id"] if x["content"] else None
#     )

#     df.to_csv(new_tracks_enriched_path)
#     print("parte 3")

#     df.drop(["recco_result"], axis=1, inplace=True)

#     df["features_recco"] = df["recco_id"].apply(
#         lambda x: get_recco_audio_features(x) if x else None)

#     df_features = df.copy()[["track_name", "features", "features_recco"]]

#     features = pd.json_normalize(df["features_recco"])

#     df = pd.concat(
#         [df.drop(columns=["features_recco"]), features],
#         axis=1
#     )
    
#     df.to_csv(new_tracks_enriched_path)



# enrich_data()
