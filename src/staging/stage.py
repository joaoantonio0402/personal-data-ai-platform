import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database


def stage_streams(df: pd.DataFrame):
    engine = connect_to_database()

    df.to_sql("stg_stream", con=engine, if_exists="append", index=False)
