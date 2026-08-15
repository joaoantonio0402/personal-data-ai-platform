from datetime import datetime, timezone
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.spt_extract import extract_lastfm_data_from_date
# from transformation.spt_transform import transform_data_from_raw_json


def get_last_run_date_from_db():
    return 0
    # return int(datetime.now(timezone.utc).timestamp())


def main():
    last_run = get_last_run_date_from_db()
    today_id = extract_lastfm_data_from_date(start_date=last_run)
    print(f"Data extraída e salva em: {today_id}")
    # transform_data_from_raw_json(today_id=today_id)


if __name__ == "__main__":
    main()

# print(int(datetime.now(timezone.utc).timestamp()))