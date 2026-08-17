import pandas as pd
from pathlib import Path
import pandas as pd
import sys
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.clients import spotify_client

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

def enrich_data():

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    NEW_RECORDS_DIR = PROJECT_ROOT / "data" / "processed" / "spotify"

    df_new_artists = pd.read_csv(NEW_RECORDS_DIR / "new_artists.csv").head(10)
    df_new_albuns = pd.read_csv(NEW_RECORDS_DIR / "new_albums.csv").head(10)
    df_new_tracks = pd.read_csv(NEW_RECORDS_DIR / "new_tracks.csv").head(10)

    ### SPOTIFY ###

    sp = spotify_client.create_spotify_client(CLIENT_ID, CLIENT_SECRET)

    ## Artists ##
    df_new_artists["spotify_data"] = df_new_artists["artist_name"].apply(
        lambda x: spotify_client.get_artist_data(x, sp)
    )

    print("1")

    artist_data_spotify = pd.json_normalize(df_new_artists["spotify_data"])

    df_new_artists = pd.concat(
        [df_new_artists.drop(columns=["spotify_data"]), artist_data_spotify],
        axis=1
    )

    ## Albuns ##
    df_new_albuns["spotify_data"] = df_new_albuns.apply(
        lambda row: spotify_client.get_album_data(
            row["album_name"],
            row["artist_name"],
            sp
        ),
        axis=1
    )

    print("1")

    album_data_spotify = pd.json_normalize(df_new_albuns["spotify_data"])

    df_new_albuns = pd.concat(
        [df_new_albuns.drop(columns=["spotify_data"]), album_data_spotify],
        axis=1
    )

    ## Tracks ##
    df_new_tracks["spotify_data"] = df_new_tracks.apply(
        lambda row: spotify_client.get_track_data(
            row["track_name"],
            row["artist_name"],
            sp
        ),
        axis=1
    )

    print("1")
    
    track_data_spotify = pd.json_normalize(df_new_tracks["spotify_data"])

    df_new_tracks = pd.concat(
        [df_new_tracks.drop(columns=["spotify_data"]), track_data_spotify],
        axis=1
    )

    df_new_artists.to_csv(NEW_RECORDS_DIR / "new_artists_enriched.csv")
    df_new_albuns.to_csv(NEW_RECORDS_DIR / "new_albuns_enriched.csv")
    df_new_tracks.to_csv(NEW_RECORDS_DIR / "new_tracks_enriched.csv")

    return

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
