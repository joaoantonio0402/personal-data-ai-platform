from datetime import datetime, timezone
import sys
from pathlib import Path
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.spt_extract import extract_lastfm_data_from_date
from src.transformation.spt_transform import transform_data_from_raw_json
from src.database.connection import connect_to_database
from src.database.schema import Base
from src.staging.stage import stage_streams
from src.load.spt_load import load_dimensions
from src.control.enrichment_control import control_enrichment_queue
from src.database.create_tables import create_tables
from src.enrichment.spt_enrich import enrich_data
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
    run_id = extract_lastfm_data_from_date(start_date=last_run + 1, api_key=os.getenv("LASTFM_API_KEY"))
    print(f"Data extraída e salva em: {run_id}")
    streams = transform_data_from_raw_json(run_id=run_id)
    if streams is None or streams.empty:
        logger.info("Nenhum novo stream encontrado; pulando carga das dimensões.")
    else:
        stage_streams(streams)
        load_dimensions(streams)
        streams.to_csv("streams.csv")
    control_enrichment_queue()
    enrich_data(reprocess_failed=False, chunk_size=10)


if __name__ == "__main__":
    main()

# print(int(datetime.now(timezone.utc).timestamp()))