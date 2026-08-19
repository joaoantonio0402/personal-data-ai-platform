import os
from pathlib import Path

import pandas as pd

from src.database.connection import connect_to_database
from src.database.schema import Base
from src.database.staging import stage_streams


def load_staged_streams(source_run_id=None):
    """Load transformed streams without inserting duplicate events."""
    project_root = Path(__file__).resolve().parents[2]
    streams_path = project_root / "data" / "processed" / "spotify" / "new_streams.csv"
    streams = pd.read_csv(streams_path)
    engine = connect_to_database()
    Base.metadata.create_all(engine)

    run_id = source_run_id or os.getenv("PIPELINE_RUN_ID", "manual")
    return stage_streams(streams, source_run_id=run_id, engine=engine)


if __name__ == "__main__":
    inserted = load_staged_streams()
    print(f"Streams novas aceitas no staging: {inserted}")