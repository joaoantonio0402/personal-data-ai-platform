import sys
from pathlib import Path
from sqlalchemy import inspect, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database

from src.database.schema import Base


LEGACY_FEATURE_COLUMNS = [
    "melodata_isrc",
    "melodata_title",
    "melodata_artist",
    "melodata_bpm",
    "melodata_key",
    "melodata_key_confidence",
    "melodata_energy",
    "melodata_danceability",
    "melodata_valence",
    "melodata_acousticness",
    "melodata_loudness",
    "melodata_instrumentalness",
    "melodata_speechiness",
    "melodata_liveness",
    "melodata_time_signature",
    "melodata_analysis_version",
    "melodata_source",
    "reccobeats_id",
    "reccobeats_href",
    "reccobeats_isrc",
    "reccobeats_acousticness",
    "reccobeats_danceability",
    "reccobeats_energy",
    "reccobeats_instrumentalness",
    "reccobeats_key",
    "reccobeats_liveness",
    "reccobeats_loudness",
    "reccobeats_mode",
    "reccobeats_speechiness",
    "reccobeats_tempo",
    "reccobeats_valence",
]


def migrate_legacy_track_features(engine):
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM enrichment_queue WHERE method = 'melodata'")
        )

    inspector = inspect(engine)
    if not inspector.has_table("dim_track"):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("dim_track")
    }
    if not set(LEGACY_FEATURE_COLUMNS).issubset(existing_columns):
        return

    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO track_audio_features (
                track_id,
                provider,
                provider_track_id,
                provider_href,
                provider_isrc,
                acousticness,
                danceability,
                energy,
                instrumentalness,
                key,
                liveness,
                loudness,
                mode,
                speechiness,
                tempo,
                valence
            )
            SELECT
                track_id,
                'reccobeats',
                reccobeats_id,
                reccobeats_href,
                reccobeats_isrc,
                reccobeats_acousticness,
                reccobeats_danceability,
                reccobeats_energy,
                reccobeats_instrumentalness,
                reccobeats_key,
                reccobeats_liveness,
                reccobeats_loudness,
                reccobeats_mode,
                reccobeats_speechiness,
                reccobeats_tempo,
                reccobeats_valence
            FROM dim_track
            WHERE reccobeats_id IS NOT NULL
            ON CONFLICT (track_id, provider) DO NOTHING
        """))

        for column in LEGACY_FEATURE_COLUMNS:
            connection.execute(
                text(f'ALTER TABLE dim_track DROP COLUMN IF EXISTS "{column}"')
            )

def create_tables():
    print("Creating tables...")

    engine = connect_to_database()

    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE track_audio_features "
                "ADD COLUMN IF NOT EXISTS popularity INTEGER"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE timeline_path "
                "ADD COLUMN IF NOT EXISTS activity_id INTEGER"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE timeline_path "
                "DROP CONSTRAINT IF EXISTS timeline_path_activity_id_fkey"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE timeline_path "
                "ALTER COLUMN activity_id DROP NOT NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE track_audio_features AS features "
                "SET provider_track_id = tracks.recco_track_id "
                "FROM dim_track AS tracks "
                "WHERE features.track_id = tracks.track_id "
                "AND features.provider = 'reccobeats' "
                "AND features.provider_track_id IS NULL "
                "AND tracks.recco_track_id IS NOT NULL"
            )
        )
    migrate_legacy_track_features(engine)

    print("Done!")