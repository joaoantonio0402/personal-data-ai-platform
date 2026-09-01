import requests
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def create_spotify_client(client_id, client_secret):
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
    )

def get_track_id(song_name, artist_name, sp):
    query = f"track:{song_name} artist:{artist_name}"

    results = sp.search(
        q=query,
        type="track",
        limit=1
    )

    tracks = results["tracks"]["items"]

    if not tracks:
        return None

    return tracks[0]["id"]


def get_track_isrc(song_name, artist_name, sp):
    query = f"track:{song_name} artist:{artist_name}"

    results = sp.search(
        q=query,
        type="track",
        limit=1
    )

    tracks = results["tracks"]["items"]

    if not tracks:
        return None

    return tracks[0]["external_ids"].get("isrc")

def get_artist_data(artist_name, sp):

    query = f"artist:{artist_name}"

    results = sp.search(
        q=query,
        type="artist",
        limit=1
    )
    
    
    artists = results["artists"]["items"]

    if not artists:
        return None

    artist = artists[0]

    # return results
    return {
        "spotify_artist_id": artist["id"],
        #"artist_name": artist["name"],
        "spotify_artist_url": artist["external_urls"].get("spotify"),
        #"spotify_followers": artist["followers"]["total"],
        #"spotify_popularity": artist["popularity"],
        #"spotify_genres": artist["genres"],
    }


def get_album_data(album_name, artist_name, sp):

    query = f"album:{album_name} artist:{artist_name}"

    results = sp.search(
        q=query,
        type="album",
        limit=1
    )

    albums = results["albums"]["items"]

    if not albums:
        return None

    album = albums[0]

    return {
        "spotify_album_id": album["id"],
        #"album_name": album["name"],
        "spotify_album_type": album["album_type"],
        "spotify_total_tracks": album["total_tracks"],
        "spotify_release_date": album["release_date"],
        "spotify_release_date_precision": album["release_date_precision"],
        #"artist_id": album["artists"][0]["id"] if album["artists"] else None,
        #"artist_name": album["artists"][0]["name"] if album["artists"] else None,
        "spotify_album_url": album["external_urls"].get("spotify"),
        #"album_uri": album["uri"],
        #"image_url": album["images"][0]["url"] if album["images"] else None
    }

def get_track_data(song_name, artist_name, sp):
    query = f"track:{song_name} artist:{artist_name}"

    results = sp.search(
        q=query,
        type="track",
        limit=1
    )

    tracks = results["tracks"]["items"]

    if not tracks:
        return None

    track = tracks[0]

    artists = track["artists"]

    # Remove o artista principal da lista
    featured_artists = [
        {
            "artist_id": artist["id"],
            "artist_name": artist["name"]
        }
        for artist in artists
        if artist["name"].lower() != artist_name.lower()
    ]

    return {
        "spotify_track_id": track["id"],
        "spotify_isrc": track["external_ids"].get("isrc"),

        "spotify_has_feat": len(featured_artists) > 0,
        "spotify_artist_count": len(featured_artists),
        "spotify_featured_artists": featured_artists,

        "spotify_release_date": (
            track["album"]["release_date"]
            if track["album"]
            else None
        ),
        "spotify_duration_ms": track["duration_ms"],
        "spotify_explicit": track["explicit"],
        "spotify_track_number": track["track_number"],
        "spotify_disc_number": track["disc_number"],
        #"spotify_popularity": track["popularity"],
        "spotify_track_url": track["external_urls"].get("spotify"),
    }





# import time
# import random
# import spotipy
# from spotipy.exceptions import SpotifyException


# def search_track_(sp, artist_name, song_name, max_retries=5):

#     query = f"track:{song_name} artist:{artist_name}"

#     for attempt in range(max_retries):

#         try:

#             results = sp.search(
#                 q=query,
#                 type="track",
#                 limit=1
#             )

#             tracks = results["tracks"]["items"]

#             if not tracks:
#                 return None

#             return tracks[0]

#         except SpotifyException as e:

#             if e.http_status == 429:

#                 retry_after = 5

#                 if e.headers:
#                     retry_after = int(
#                         e.headers.get("Retry-After", retry_after)
#                     )

#                 print(
#                     f"Rate limit. Esperando {retry_after}s..."
#                 )

#                 time.sleep(retry_after)

#             else:
#                 raise

#     raise RuntimeError(
#         f"Não foi possível buscar: {artist_name} - {song_name}"
#     )




# sp = create_spotify_client(client_id="c1d9c36c51a44689844d5e5485d88693", client_secret="ac2fb90076cf4536b425298e692d19b8")
# print(get_artist_data(artist_name="J cole", sp=sp))
# print("----------------------------------------")
# print(sp.artist(artist_id="0TnOYISbd1XYRBk9myaseg"))