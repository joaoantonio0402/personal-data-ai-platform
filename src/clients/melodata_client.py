import requests
import os


BASE_URL = "https://melodata1.p.rapidapi.com"

HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "melodata1.p.rapidapi.com"
}
api_key = os.getenv(MELODATA_API_KEY)

def get_track_features(isrc):
    """
    Retrieve audio features for a track using its ISRC.

    Args:
        isrc: International Standard Recording Code.
        api_key: RapidAPI key.

    Returns:
        JSON response containing track features.
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

    return response.json()


def search_track(song_name, api_key, limit=10, offset=0):
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

