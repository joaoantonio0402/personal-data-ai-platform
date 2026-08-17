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

    return {
        "artist_id_spotify": artist["id"],
        #"artist_name": artist["name"],
        "artist_url": artist["external_urls"].get("spotify"),
        "followers": artist["followers"]["total"],
        "popularity": artist["popularity"],
        "genres": artist["genres"],
        "artist_uri": artist["uri"]
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
        "album_id": album["id"],
        #"album_name": album["name"],
        "album_type": album["album_type"],
        "total_tracks": album["total_tracks"],
        "release_date": album["release_date"],
        "release_date_precision": album["release_date_precision"],
        #"artist_id": album["artists"][0]["id"] if album["artists"] else None,
        #"artist_name": album["artists"][0]["name"] if album["artists"] else None,
        "album_url": album["external_urls"].get("spotify"),
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

    return {
        "track_id": track["id"],
        "isrc": track["external_ids"].get("isrc"),
        #"track_name": track["name"],
        #"artist_id": track["artists"][0]["id"] if track["artists"] else None,
        #"artist_name": track["artists"][0]["name"] if track["artists"] else None,
        #"album_id": track["album"]["id"] if track["album"] else None,
        #"album_name": track["album"]["name"] if track["album"] else None,
        #"album_type": track["album"]["album_type"] if track["album"] else None,
        "release_date": track["album"]["release_date"] if track["album"] else None,
        "duration_ms": track["duration_ms"],
        "explicit": track["explicit"],
        "track_number": track["track_number"],
        "disc_number": track["disc_number"],
        "popularity": track["popularity"],
        "track_url": track["external_urls"].get("spotify"),
        #"track_uri": track["uri"],
        #"preview_url": track["preview_url"]
    }

