import json
import logging

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.schema import DimAlbum, DimArtist, DimTrack, FactListening


logger = logging.getLogger(__name__)


def _value(value):
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True)
    return value.item() if hasattr(value, "item") else value


def _first_value(row, *names):
    for name in names:
        if name in row and _value(row[name]) is not None:
            return _value(row[name])
    return None


def _attributes(row, model):
    attributes = {}
    for column in model.__table__.columns:
        if column.primary_key or column.name in {"artist_id", "album_id", "track_id"}:
            continue
        value = _first_value(
            row,
            column.name,
            f"melodata_{column.name}",
            f"reccobeats_{column.name}",
        )
        if value is not None:
            attributes[column.name] = value
    return attributes


def _upsert(session, model, key_name, key, attributes):
    instance = session.scalar(select(model).where(getattr(model, key_name) == key))
    if instance is None:
        instance = model(**{key_name: key})
        session.add(instance)
    for name, value in attributes.items():
        setattr(instance, name, value)
    return instance


def load_enriched_data(engine, streams, artists, albums, tracks):
    """Upsert enriched dimensions and insert listening facts transactionally."""
    artist_ids = {}
    album_ids = {}
    track_ids = {}
    counts = {"artists": 0, "albums": 0, "tracks": 0, "streams": 0}

    with Session(engine) as session, session.begin():
        for _, row in artists.iterrows():
            artist_key = _first_value(row, "artist_key")
            if not artist_key:
                raise ValueError(f"Artist without artist_key: {row.get('artist_name')}")
            artist = _upsert(
                session, DimArtist, "artist_key", artist_key,
                _attributes(row, DimArtist),
            )
            session.flush()
            artist_ids[artist_key] = artist.artist_id
            counts["artists"] += 1

        for _, row in albums.iterrows():
            album_key = _first_value(row, "album_key")
            artist_key = _first_value(row, "artist_key")
            if not album_key or artist_key not in artist_ids:
                raise ValueError(f"Album relationship is incomplete: {row.get('album_name')}")
            attributes = _attributes(row, DimAlbum)
            attributes["artist_id"] = artist_ids[artist_key]
            album = _upsert(session, DimAlbum, "album_key", album_key, attributes)
            session.flush()
            album_ids[album_key] = album.album_id
            counts["albums"] += 1

        for _, row in tracks.iterrows():
            track_key = _first_value(row, "track_key")
            artist_key = _first_value(row, "artist_key")
            album_key = _first_value(row, "album_key")
            if not track_key or artist_key not in artist_ids or album_key not in album_ids:
                raise ValueError(f"Track relationship is incomplete: {row.get('track_name')}")
            attributes = _attributes(row, DimTrack)
            attributes["artist_id"] = artist_ids[artist_key]
            attributes["album_id"] = album_ids[album_key]
            track = _upsert(session, DimTrack, "track_key", track_key, attributes)
            session.flush()
            track_ids[track_key] = track.track_id
            counts["tracks"] += 1

        for _, row in streams.iterrows():
            source_event_id = _first_value(row, "source_event_id")
            track_key = _first_value(row, "track_key")
            if not source_event_id or track_key not in track_ids:
                raise ValueError(f"Stream relationship is incomplete: {source_event_id}")
            exists = session.scalar(
                select(FactListening).where(
                    FactListening.source_event_id == source_event_id
                )
            )
            if exists is None:
                session.add(
                    FactListening(
                        track_id=track_ids[track_key],
                        source_event_id=source_event_id,
                        timestamp_utc=_value(row.get("timestamp_utc")),
                        timestamp_uts=_value(row.get("timestamp_uts")),
                        track_url=_value(row.get("track_url")),
                    )
                )
                counts["streams"] += 1

    return counts