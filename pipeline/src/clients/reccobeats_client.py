import requests


BASE_URL = "https://api.reccobeats.com/v1"

HEADERS = {
    "Accept": "application/json"
}


def _normalize_text(value):
    text = (value or "").strip().lower()
    replacements = {
        "&": " and ",
        "/": " ",
        "-": " ",
        "_": " ",
        ".": " ",
        ",": " ",
        "!": " ",
        "?": " ",
        "(": " ",
        ")": " ",
        "'": "",
        '"': "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split())


def _iter_search_results(payload):
    if not isinstance(payload, dict):
        return []

    for key in ("content", "items", "tracks", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = value.get("items") or value.get("tracks") or value.get("content") or []
            if isinstance(nested, list):
                return nested
    return []


def _track_matches(track_name, artist_name, track):
    if not isinstance(track, dict):
        return False

    raw_title = track.get("trackTitle") or track.get("name") or track.get("title") or ""
    raw_artists = track.get("artists") or []

    normalized_track_name = _normalize_text(track_name)
    normalized_title = _normalize_text(raw_title)

    title_match = (
        normalized_title == normalized_track_name
        or normalized_track_name in normalized_title
        or normalized_title in normalized_track_name
    )
    if not title_match:
        return False

    artists = []
    for artist in raw_artists:
        if isinstance(artist, dict):
            artists.append(_normalize_text(artist.get("name")))
        else:
            artists.append(_normalize_text(artist))

    if not artist_name:
        return True

    normalized_artist_name = _normalize_text(artist_name)
    if normalized_artist_name in artists:
        return True

    artist_alias = normalized_artist_name.replace(" ", "")
    return any(artist_alias in artist.replace(" ", "") for artist in artists)


def _extract_track_id(track_id):
    if not track_id:
        return None

    if isinstance(track_id, dict):
        for key in ("id", "track_id", "trackId"):
            value = track_id.get(key)
            if value:
                return str(value)
        nested = track_id.get("search") or track_id.get("track") or {}
        if isinstance(nested, dict):
            value = nested.get("id") or nested.get("track_id") or nested.get("trackId")
            if value:
                return str(value)
        return None

    value = str(track_id).strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value.rstrip("/").split("/")[-1] or None
    return value


def _coerce_audio_payload(data):
    if not isinstance(data, dict):
        return {}

    if isinstance(data.get("audio_features"), dict):
        return data["audio_features"]
    if isinstance(data.get("features"), dict):
        return data["features"]
    if isinstance(data.get("data"), dict):
        return data["data"]
    if isinstance(data.get("track"), dict):
        return data["track"]
    if isinstance(data.get("audioFeatures"), dict):
        return data["audioFeatures"]
    if isinstance(data.get("search"), dict):
        search_payload = data["search"]
        if isinstance(search_payload.get("audio_features"), dict):
            return search_payload["audio_features"]
        if isinstance(search_payload.get("features"), dict):
            return search_payload["features"]
        return search_payload
    return data


def search_track(track_name, artist_name):
    """
    Search for a track on ReccoBeats by track name and artist.

    Args:
        track_name: Name of the track.
        artist_name: Name of the artist.

    Returns:
        Matching track as a dictionary, or None if no match is found.
    """
    if not track_name:
        return None

    url = f"{BASE_URL}/track/search"
    params = {"searchText": track_name}

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json() or {}
    if isinstance(data, dict) and "search" in data and isinstance(data.get("search"), dict):
        track = data["search"]
        if _track_matches(track_name, artist_name, track):
            return track

    results = _iter_search_results(data)
    for track in results:
        if _track_matches(track_name, artist_name, track):
            return track

    if artist_name:
        return None

    return results[0] if results else None


def get_audio_features(track_id):
    """
    Retrieve audio features for a ReccoBeats track.

    Args:
        track_id: ReccoBeats track ID.

    Returns:
        Dictionary containing ReccoBeats audio features with
        `reccobeats_` prefixes.
    """
    normalized_track_id = _extract_track_id(track_id)
    if not normalized_track_id:
        return None

    urls = [
        f"{BASE_URL}/track/{normalized_track_id}/audio-features",
        f"{BASE_URL}/track/{normalized_track_id}/features",
        f"{BASE_URL}/tracks/{normalized_track_id}/audio-features",
        f"{BASE_URL}/tracks/{normalized_track_id}/features",
    ]

    last_error = None
    for url in urls:
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20,
            )
            if response.status_code == 404:
                last_error = response
                continue
            response.raise_for_status()
            data = response.json() or {}
            payload = _coerce_audio_payload(data)
            if not payload:
                continue

            return {
                "reccobeats_id": payload.get("id") or normalized_track_id,
                "reccobeats_href": payload.get("href"),
                "reccobeats_isrc": payload.get("isrc"),
                "reccobeats_acousticness": payload.get("acousticness"),
                "reccobeats_danceability": payload.get("danceability"),
                "reccobeats_energy": payload.get("energy"),
                "reccobeats_instrumentalness": payload.get("instrumentalness"),
                "reccobeats_key": payload.get("key"),
                "reccobeats_liveness": payload.get("liveness"),
                "reccobeats_loudness": payload.get("loudness"),
                "reccobeats_mode": payload.get("mode"),
                "reccobeats_speechiness": payload.get("speechiness"),
                "reccobeats_tempo": payload.get("tempo"),
                "reccobeats_valence": payload.get("valence"),
            }
        except requests.RequestException as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    return None


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