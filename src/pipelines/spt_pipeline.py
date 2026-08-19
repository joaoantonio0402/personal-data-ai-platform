from datetime import datetime, timezone
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.spt_extract import extract_lastfm_data_from_date
from src.transformation.spt_transform import transform_data_from_raw_json
from src.database.connection import connect_to_database
from src.database.schema import Base
from src.database.staging import get_last_stream_timestamp, stage_streams


def get_last_run_date_from_db():
    engine = connect_to_database()
    Base.metadata.create_all(engine)
    return get_last_stream_timestamp(engine)


def main():
    engine = connect_to_database()
    Base.metadata.create_all(engine)
    last_run = get_last_stream_timestamp(engine)
    today_id = extract_lastfm_data_from_date(start_date=last_run + 1)
    print(f"Data extraída e salva em: {today_id}")
    streams = transform_data_from_raw_json(id=today_id)
    inserted = stage_streams(streams, source_run_id=today_id, engine=engine)
    print(f"Streams novas aceitas no staging: {inserted}")


if __name__ == "__main__":
    main()

# print(int(datetime.now(timezone.utc).timestamp()))