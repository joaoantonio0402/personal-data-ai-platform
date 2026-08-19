from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.database.schema import EnrichmentJob, StgStream


ENRICHMENT_PROVIDERS = ("spotify", "melodata", "reccobeats")


def get_last_stream_timestamp(engine):
    """Return the latest timestamp already accepted by staging."""
    with engine.connect() as connection:
        value = connection.execute(
            select(func.max(StgStream.timestamp_uts))
        ).scalar_one()
    return int(value or 0)


def stage_streams(df, source_run_id, engine):
    """Insert normalized streams once and enqueue their track enrichments."""
    if df.empty:
        return 0

    records = df.copy()
    records["timestamp_utc"] = (
        pd.to_datetime(records["timestamp_utc"], utc=True)
        .dt.tz_localize(None)
    )
    records["source_run_id"] = source_run_id
    records["source_event_id"] = records.apply(create_source_event_id, axis=1)
    records = records.drop_duplicates(subset="source_event_id")

    stream_columns = [
        "source_event_id", "source_run_id", "track_mbid", "track_name",
        "artist_mbid", "artist_name", "album_mbid", "album_name",
        "track_key", "artist_key", "album_key", "timestamp_utc",
        "timestamp_uts", "track_url", "streamable",
    ]
    stream_rows = records[stream_columns].where(pd.notna(records[stream_columns]), None)
    job_rows = [
        {"track_key": track_key, "provider": provider, "status": "pending", "attempts": 0}
        for track_key in records["track_key"].dropna().unique()
        for provider in ENRICHMENT_PROVIDERS
    ]

    with engine.begin() as connection:
        insert_for_dialect = (
            sqlite_insert if connection.dialect.name == "sqlite" else postgres_insert
        )
        stream_statement = insert_for_dialect(StgStream).values(
            stream_rows.to_dict("records")
        )
        inserted = stream_statement.on_conflict_do_nothing(
            index_elements=[StgStream.source_event_id]
        )
        result = connection.execute(inserted)

        if job_rows:
            job_statement = insert_for_dialect(EnrichmentJob).values(job_rows)
            connection.execute(
                job_statement.on_conflict_do_nothing(
                    index_elements=[EnrichmentJob.track_key, EnrichmentJob.provider]
                )
            )

    return result.rowcount


def create_source_event_id(row):
    track_identity = row.get("track_mbid") or row.get("track_key")
    url = row.get("track_url") or ""
    return f"lastfm:{row['timestamp_uts']}:{track_identity}:{url}"


def get_pending_track_keys(engine):
    with engine.connect() as connection:
        rows = connection.execute(
            select(EnrichmentJob.track_key).where(
                EnrichmentJob.status.in_(("pending", "failed"))
            )
        )
    return {row[0] for row in rows}


def get_pending_tracks(engine):
    pending_track_keys = get_pending_track_keys(engine)
    if not pending_track_keys:
        return pd.DataFrame()

    with engine.connect() as connection:
        return pd.read_sql(
            select(StgStream).where(StgStream.track_key.in_(pending_track_keys)),
            connection,
        )


def mark_jobs_completed(engine, track_keys):
    if not track_keys:
        return 0

    with engine.begin() as connection:
        result = connection.execute(
            update(EnrichmentJob)
            .where(
                EnrichmentJob.track_key.in_(track_keys),
                EnrichmentJob.status.in_(("pending", "failed")),
            )
            .values(
                status="completed",
                enriched_at=datetime.now(timezone.utc).replace(tzinfo=None),
                last_error=None,
            )
        )
    return result.rowcount


def mark_job_completed(session, track_key, provider):
    job = session.execute(
        select(EnrichmentJob).where(
            EnrichmentJob.track_key == track_key,
            EnrichmentJob.provider == provider,
        )
    ).scalar_one()
    job.status = "completed"
    job.enriched_at = datetime.now(timezone.utc)
    job.last_error = None