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
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'stg_stream'
                          AND column_name = 'timestamp_utc'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE stg_stream
                        ALTER COLUMN timestamp_utc TYPE TIMESTAMPTZ
                        USING timestamp_utc AT TIME ZONE 'UTC';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'fact_listening'
                          AND column_name = 'timestamp_utc'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE fact_listening
                        ALTER COLUMN timestamp_utc TYPE TIMESTAMPTZ
                        USING timestamp_utc AT TIME ZONE 'UTC';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'fact_visit'
                          AND column_name = 'start_time'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE fact_visit
                        ALTER COLUMN start_time TYPE TIMESTAMPTZ
                        USING start_time AT TIME ZONE 'America/Sao_Paulo';
                        ALTER TABLE fact_visit
                        ALTER COLUMN end_time TYPE TIMESTAMPTZ
                        USING end_time AT TIME ZONE 'America/Sao_Paulo';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'fact_activity'
                          AND column_name = 'start_time'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE fact_activity
                        ALTER COLUMN start_time TYPE TIMESTAMPTZ
                        USING start_time AT TIME ZONE 'America/Sao_Paulo';
                        ALTER TABLE fact_activity
                        ALTER COLUMN end_time TYPE TIMESTAMPTZ
                        USING end_time AT TIME ZONE 'America/Sao_Paulo';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'timeline_path'
                          AND column_name = 'start_time'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE timeline_path
                        ALTER COLUMN start_time TYPE TIMESTAMPTZ
                        USING start_time AT TIME ZONE 'America/Sao_Paulo';
                        ALTER TABLE timeline_path
                        ALTER COLUMN end_time TYPE TIMESTAMPTZ
                        USING end_time AT TIME ZONE 'America/Sao_Paulo';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'fact_context_event'
                          AND column_name = 'timestamp'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE fact_context_event
                        ALTER COLUMN timestamp TYPE TIMESTAMPTZ
                        USING timestamp AT TIME ZONE 'UTC';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'fact_context_event'
                          AND column_name = 'created_at'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE fact_context_event
                        ALTER COLUMN created_at TYPE TIMESTAMPTZ
                        USING created_at AT TIME ZONE 'UTC';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'context_queue'
                          AND column_name = 'queued_at'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE context_queue
                        ALTER COLUMN queued_at TYPE TIMESTAMPTZ
                        USING queued_at AT TIME ZONE 'UTC';
                        ALTER TABLE context_queue
                        ALTER COLUMN processed_at TYPE TIMESTAMPTZ
                        USING processed_at AT TIME ZONE 'UTC';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'enrichment_queue'
                          AND column_name = 'enriched_at'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE enrichment_queue
                        ALTER COLUMN enriched_at TYPE TIMESTAMPTZ
                        USING enriched_at AT TIME ZONE 'UTC';
                    END IF;

                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'track_audio_features'
                          AND column_name = 'fetched_at'
                          AND data_type = 'timestamp without time zone'
                    ) THEN
                        ALTER TABLE track_audio_features
                        ALTER COLUMN fetched_at TYPE TIMESTAMPTZ
                        USING fetched_at AT TIME ZONE 'UTC';
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                "UPDATE stg_stream "
                "SET timestamp_utc = to_timestamp(timestamp_uts) "
                "WHERE timestamp_uts IS NOT NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE fact_listening "
                "SET timestamp_utc = to_timestamp(timestamp_uts) "
                "WHERE timestamp_uts IS NOT NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE fact_context_event AS events "
                "SET timestamp = listenings.timestamp_utc "
                "FROM fact_listening AS listenings "
                "WHERE events.listening_id = listenings.listening_id"
            )
        )
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
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS match_method TEXT"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS match_score DOUBLE PRECISION"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS time_distance_seconds INTEGER"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS overlap_seconds INTEGER"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS context_type TEXT"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS track_name TEXT"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS start_latitude DOUBLE PRECISION"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS start_longitude DOUBLE PRECISION"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS end_latitude DOUBLE PRECISION"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS end_longitude DOUBLE PRECISION"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS location_source TEXT"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS location_precision TEXT"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS google_maps_url TEXT"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE fact_context_event "
                "ALTER COLUMN timestamp DROP NOT NULL"
            )
        )
        connection.execute(
            text(
                "DELETE FROM fact_context_event AS duplicate "
                "USING fact_context_event AS original "
                "WHERE duplicate.listening_id = original.listening_id "
                "AND duplicate.event_id > original.event_id"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_context_event_listening "
                "ON fact_context_event (listening_id)"
            )
        )
        connection.execute(
            text(
                "DELETE FROM fact_listening AS duplicate "
                "USING fact_listening AS original "
                "WHERE duplicate.listening_id > original.listening_id "
                "AND duplicate.track_id = original.track_id "
                "AND duplicate.timestamp_uts = original.timestamp_uts"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_fact_listening_track_timestamp "
                "ON fact_listening (track_id, timestamp_uts)"
            )
        )
    migrate_legacy_track_features(engine)

    print("Done!")