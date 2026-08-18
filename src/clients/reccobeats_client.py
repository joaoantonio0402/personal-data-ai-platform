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
        Dictionary containing ReccoBeats audio features with
        `reccobeats_` prefixes.
    """

    url = f"{BASE_URL}/track/{track_id}/audio-features"

    response = requests.get(
        url,
        headers=HEADERS
    )

    response.raise_for_status()

    data = response.json()

    return {
        "reccobeats_id": data.get("id"),
        "reccobeats_href": data.get("href"),
        "reccobeats_isrc": data.get("isrc"),

        "reccobeats_acousticness": data.get("acousticness"),
        "reccobeats_danceability": data.get("danceability"),
        "reccobeats_energy": data.get("energy"),
        "reccobeats_instrumentalness": data.get("instrumentalness"),
        "reccobeats_key": data.get("key"),
        "reccobeats_liveness": data.get("liveness"),
        "reccobeats_loudness": data.get("loudness"),
        "reccobeats_mode": data.get("mode"),
        "reccobeats_speechiness": data.get("speechiness"),
        "reccobeats_tempo": data.get("tempo"),
        "reccobeats_valence": data.get("valence"),
    }


# print(get_audio_features(track_id="24bb9d1d-40ce-4f42-9516-c4f40b1e4fd6"))









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