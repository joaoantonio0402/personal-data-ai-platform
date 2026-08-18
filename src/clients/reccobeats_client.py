import requests


BASE_URL = "https://api.reccobeats.com/v1"

HEADERS = {
    "Accept": "application/json"
}


def search_track(track_name, artist_name):
    """
    Search for a track on ReccoBeats.

    Args:
        track_name: Name of the track.
        artist_name: Name of the artist.

    Returns:
        JSON response from ReccoBeats.
    """

    url = f"{BASE_URL}/track/search"

    params = {
        "searchText": track_name,
        "artist": artist_name
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS
    )

    response.raise_for_status()

    return response.json()


def get_audio_features(track_id):
    """
    Retrieve audio features for a ReccoBeats track.

    Args:
        track_id: ReccoBeats track ID.

    Returns:
        JSON response containing audio features.
    """

    url = f"{BASE_URL}/track/{track_id}/audio-features"

    response = requests.get(
        url,
        headers=HEADERS
    )

    response.raise_for_status()

    return response.json()












# import requests

# BASE_URL = "https://api.reccobeats.com/v1"

# def get_recco_audio_features(track_id):
#     url = f"/track/{track_id}/audio-features"

#     headers = {
#         "Accept": "application/json"
#     }

#     response = requests.get(
#         url,
#         headers=headers
#     )

#     response.raise_for_status()

#     return response.json()


# def search_recco_safe(row):
#     try:
#         return search_recco(row["track_name"], row["artist_name"])
#     except Exception as e:
#         print(
#             f"Erro: {row['artist_name']} - "
#             f"{row['track_name']} - "
#             f"{row['isrc']} | {e}"
#         )
#         return None

# def search_recco(track_name, artist_name):
#     url = "https://api.reccobeats.com/v1/track/search"

#     params = {
#         "searchText": track_name,
#         "artist": artist_name
#     }

#     response = requests.get(url, params=params)
#     response.raise_for_status()

#     return response.json()