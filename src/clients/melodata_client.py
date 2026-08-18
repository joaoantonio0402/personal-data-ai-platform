import requests
import os

# API_KEY = os.getenv("MELODATA_API_KEY")

BASE_URL = "https://melodata1.p.rapidapi.com"

HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "melodata1.p.rapidapi.com"
}

def get_track_features(api_key, isrc):
    """
    Retrieve audio features for a track using its ISRC.

    Args:
        api_key: RapidAPI key.
        isrc: International Standard Recording Code.

    Returns:
        Dictionary containing Melodata track features with
        `melodata_` prefixes.
    """

    url = f"{BASE_URL}/tracks/{isrc}/features"

    headers = {
        **HEADERS,
        "x-rapidapi-key": api_key
    }

    response = requests.get(
        url,
        headers=headers
    )

    response.raise_for_status()

    data = response.json()["data"]
    features = data["features"]

    return {
        "melodata_isrc": data.get("isrc"),
        "melodata_title": data.get("title"),
        "melodata_artist": data.get("artist"),

        "melodata_bpm": features.get("bpm"),
        "melodata_key": features.get("key"),
        "melodata_key_confidence": features.get("key_confidence"),
        "melodata_energy": features.get("energy"),
        "melodata_danceability": features.get("danceability"),
        "melodata_valence": features.get("valence"),
        "melodata_acousticness": features.get("acousticness"),
        "melodata_loudness": features.get("loudness"),
        "melodata_instrumentalness": features.get("instrumentalness"),
        "melodata_speechiness": features.get("speechiness"),
        "melodata_liveness": features.get("liveness"),
        "melodata_time_signature": features.get("time_signature"),

        "melodata_analysis_version": data.get("analysis_version"),
        "melodata_source": data.get("source"),
    }


def search_track(api_key, song_name, limit=10, offset=0):
    """
    Search for tracks on Melodata.

    Args:
        song_name: Track name or search query.
        api_key: RapidAPI key.
        limit: Maximum number of results.
        offset: Pagination offset.

    Returns:
        JSON response containing search results.
    """

    url = f"{BASE_URL}/tracks/search"

    params = {
        "q": song_name,
        "offset": offset,
        "limit": limit
    }

    headers = {
        **HEADERS,
        "x-rapidapi-key": api_key
    }

    response = requests.get(
        url,
        params=params,
        headers=headers
    )

    response.raise_for_status()

    return response.json()

# print(get_track_features(api_key="dbcd34ab68mshbdcca93581f9718p1c56b8jsn2fe95019b903", isrc="GBBKS1000352"))






# def get_track_features(isrc):
#     url = f"https://melodata1.p.rapidapi.com/tracks/{isrc}/features"

#     headers = {
#         "Content-Type": "application/json",
#         "x-rapidapi-host": "melodata1.p.rapidapi.com",
#         "x-rapidapi-key": "dbcd34ab68mshbdcca93581f9718p1c56b8jsn2fe95019b903"
#     }

#     response = requests.get(
#         url,
#         headers=headers
#     )

#     response.raise_for_status()

#     return response.json()

# def search_track(song_name, limit=10, offset=0):

#     url = "https://melodata1.p.rapidapi.com/tracks/search"

#     params = {
#         "q": song_name,
#         "offset": offset,
#         "limit": limit
#     }

#     headers = {
#         "Content-Type": "application/json",
#         "x-rapidapi-host": "melodata1.p.rapidapi.com",
#         "x-rapidapi-key": "dbcd34ab68mshbdcca93581f9718p1c56b8jsn2fe95019b903"
#     }

#     response = requests.get(
#         url,
#         params=params,
#         headers=headers
#     )

#     response.raise_for_status()

#     return response.json()


# def get_features_safe(row):
#     try:
#         return get_track_features(row["isrc"])
#     except Exception as e:
#         print(
#             f"Erro: {row['artist_name']} - "
#             f"{row['track_name']} - "
#             f"{row['isrc']} | {e}"
#         )
#         return None

