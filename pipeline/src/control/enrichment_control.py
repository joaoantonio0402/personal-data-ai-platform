from pathlib import Path
import sys
import json
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import select, update

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database
from src.database.schema import Base, Candidates, EnrichmentQueue, StgStream

def parse_stream_to_enrich_df(row):
    columns = ["enrichment_name", "type", "method", "info", "enriched_at", "status"]
    enrichments = []

    def add_enrichment(name, enrichment_type, method):
        if pd.notna(name) and str(name).strip():
            enrichments.append(
                {
                    "enrichment_name": name,
                    "type": enrichment_type,
                    "method": method,
                    "info": None,
                    "enriched_at": None,
                    "status": "pending",
                }
            )

    add_enrichment(row.get("artist_name"), "artist", "spotify")
    add_enrichment(row.get("album_name"), "album", "spotify")
    add_enrichment(row.get("track_name"), "track", "spotify")
    add_enrichment(row.get("track_name"), "track", "reccobeats")

    return pd.DataFrame(enrichments, columns=columns)


def control_enrichment_queue():
    columns = ["enrichment_name", "type", "method", "info", "enriched_at", "status"]
    engine = connect_to_database()
    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        streams_df = pd.read_sql(
            select(
                StgStream.track_name,
                StgStream.artist_name,
                StgStream.album_name,
            ).distinct(),
            connection,
        )
        candidates_df = pd.read_sql(
            select(Candidates.candidate_id),
            connection,
        )

    parsed_frames = [
        parse_stream_to_enrich_df(row)
        for _, row in streams_df.iterrows()
    ]
    enrichments_df = (
        pd.concat(parsed_frames, ignore_index=True)
        if parsed_frames
        else pd.DataFrame(columns=columns)
    )
    google_enrichments_df = pd.DataFrame(
        {
            "enrichment_name": candidates_df["candidate_id"],
            "type": "candidate",
            "method": "google",
            "info": None,
            "enriched_at": None,
            "status": "pending",
        }
    )
    enrichments_df = pd.concat(
        [enrichments_df, google_enrichments_df], ignore_index=True
    )
    enrichments_df = enrichments_df.drop_duplicates(
        subset=["enrichment_name", "type", "method"]
    )

    with engine.connect() as connection:
        existing = pd.read_sql(
            select(
                EnrichmentQueue.enrichment_name,
                EnrichmentQueue.type,
                EnrichmentQueue.method,
            ),
            connection,
        )

    if existing.empty:
        new_enrichments_df = enrichments_df
    else:
        existing_keys = pd.MultiIndex.from_frame(
            existing[["enrichment_name", "type", "method"]]
        )
        candidate_keys = pd.MultiIndex.from_frame(
            enrichments_df[["enrichment_name", "type", "method"]]
        )
        new_enrichments_df = enrichments_df[
            ~candidate_keys.isin(existing_keys)
        ]

    if not new_enrichments_df.empty:
        new_enrichments_df.to_sql(
            EnrichmentQueue.__tablename__,
            con=engine,
            if_exists="append",
            index=False,
        )

    return new_enrichments_df.reset_index(drop=True)


def serialize_api_response(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return json.dumps(value, ensure_ascii=False, default=str)


def mark_enrichments_completed(dim):
    """Mark processed queue entries as completed or failed."""
    engine = connect_to_database()
    processed_at = datetime.now(timezone.utc)

    enrichment_specs = [
        ("artist", "spotify", dim["artist"], "artist_name", "spotify_artist_id", "spotify_required", "spotify_api_response"),
        ("album", "spotify", dim["album"], "album_name", "spotify_album_id", "spotify_required", "spotify_api_response"),
        ("track", "spotify", dim["track"], "track_name", "spotify_track_id", "spotify_required", "spotify_api_response"),
        ("track", "reccobeats", dim["track"], "track_name", "recco_track_id", "reccobeats_required", "reccobeats_api_response"),
    ]

    with engine.begin() as connection:
        for enrichment_type, method, dataframe, name_column, result_column, required_column, response_column in enrichment_specs:
            if name_column not in dataframe:
                continue

            names = dataframe[name_column].fillna("").astype(str).str.strip()
            required = dataframe[required_column] if required_column in dataframe else True
            succeeded = (
                dataframe[result_column]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                if result_column in dataframe
                else pd.Series(False, index=dataframe.index)
            )

            for (_, row), name, should_process, success in zip(dataframe.iterrows(), names, required, succeeded):
                if not name or not should_process:
                    continue
                connection.execute(
                    update(EnrichmentQueue)
                    .where(
                        EnrichmentQueue.enrichment_name == name,
                        EnrichmentQueue.type == enrichment_type,
                        EnrichmentQueue.method == method,
                        EnrichmentQueue.status.in_(["pending", "failed"]),
                    )
                    .values(
                        status="completed" if success else "failed",
                        enriched_at=processed_at,
                        info=serialize_api_response(row.get(response_column)),
                    )
                )
