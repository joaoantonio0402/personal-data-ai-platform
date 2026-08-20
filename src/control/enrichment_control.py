from pathlib import Path
import sys
import pandas as pd
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database
from src.database.schema import Base, EnrichmentQueue, StgStream

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
    add_enrichment(row.get("track_name"), "track", "melodata")
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

    parsed_frames = [
        parse_stream_to_enrich_df(row)
        for _, row in streams_df.iterrows()
    ]
    enrichments_df = (
        pd.concat(parsed_frames, ignore_index=True)
        if parsed_frames
        else pd.DataFrame(columns=columns)
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


control_enrichment_queue()
