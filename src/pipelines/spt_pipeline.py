from datetime import datetime, timezone
import sys
from pathlib import Path
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.spt_extract import extract_lastfm_data_from_date
from src.transformation.spt_transform import transform_data_from_raw_json
from src.database.connection import connect_to_database
from src.database.schema import Base
from src.staging.stage import stage_streams
from src.control.enrichment_control import (
    control_enrichment_queue,
    mark_enrichments_completed,
)
from src.database.create_tables import create_tables
from src.enrichment.spt_enrich import enrich_data
from src.load.spt_load import load_enriched_data
import logging

from src.database.schema import StgStream

def get_last_stream_timestamp(engine):
    """Return the latest timestamp already accepted by staging."""
    with engine.connect() as connection:
        value = connection.execute(
            select(func.max(StgStream.timestamp_uts))
        ).scalar_one()
    return int(value or 0)



def get_last_run_date_from_db():
    engine = connect_to_database()
    Base.metadata.create_all(engine)
    return get_last_stream_timestamp(engine)


def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)

    create_tables()
    last_run = get_last_run_date_from_db()
    run_id = extract_lastfm_data_from_date(start_date=last_run + 1)
    print(f"Data extraída e salva em: {run_id}")
    streams = transform_data_from_raw_json(run_id=run_id)
    stage_streams(streams)
    streams.to_csv("streams.csv")
    control_enrichment_queue()
    enriched_data = enrich_data(reprocess_failed=True)
    dimensions = {
        "artist": enriched_data["artists"],
        "album": enriched_data["albums"],
        "track": enriched_data["tracks"],
    }
    load_enriched_data(
        fact_listening=enriched_data["streams"],
        dim=dimensions,
    )
    mark_enrichments_completed(dimensions)


if __name__ == "__main__":
    main()

# print(int(datetime.now(timezone.utc).timestamp()))