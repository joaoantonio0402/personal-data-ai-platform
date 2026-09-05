from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database
from src.database.schema import Base


def _filter_new_rows_by_start_time(engine, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or "start_time" not in df.columns:
        return df

    with engine.begin() as connection:
        max_ts = connection.execute(
            text(f"SELECT MAX(start_time) FROM {table_name}")
        ).scalar()

    if pd.isna(max_ts) or max_ts is None:
        return df

    df = df.copy()
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")

    timezone_name = "America/Sao_Paulo"
    if getattr(df["start_time"].dt, "tz", None) is None:
        df["start_time"] = df["start_time"].dt.tz_localize(timezone_name)
    else:
        df["start_time"] = df["start_time"].dt.tz_convert(timezone_name)

    max_ts = pd.to_datetime(max_ts, errors="coerce")
    if getattr(max_ts, "tzinfo", None) is None:
        max_ts = max_ts.tz_localize(timezone_name)
    else:
        max_ts = max_ts.tz_convert(timezone_name)

    return df[df["start_time"] > max_ts].copy()


def _insert_if_new(engine, table_name: str, df: pd.DataFrame, unique_columns=None):
    if df is None or df.empty:
        return 0

    df = df.copy()

    if unique_columns is not None:
        df = df.drop_duplicates(subset=list(unique_columns)).copy()
    elif "candidate_id" in df.columns:
        df = df.drop_duplicates(subset=["candidate_id"]).copy()
    elif "activity_id" in df.columns and "start_time" in df.columns and "end_time" in df.columns:
        df = df.drop_duplicates(subset=["activity_id", "start_time", "end_time"]).copy()

    if table_name in {"fact_visit", "fact_activity", "timeline_path"}:
        df = _filter_new_rows_by_start_time(engine, table_name, df)

    if table_name == "dim_candidates":
        with engine.begin() as connection:
            existing = pd.read_sql(
                "SELECT candidate_id FROM dim_candidates",
                connection,
            )
            if not existing.empty:
                existing_ids = set(existing["candidate_id"].dropna().astype(str))
                df = df[~df["candidate_id"].fillna("").astype(str).isin(existing_ids)].copy()

        if df.empty:
            return 0

    if df.empty:
        return 0

    df.to_sql(table_name, con=engine, if_exists="append", index=False)
    return len(df)


def load_google_data(data: dict) -> dict:
    """Persist Google Timeline tables into Postgres using the same pattern as the Spotify pipeline."""
    engine = connect_to_database()
    Base.metadata.create_all(engine)

    candidates = data.get("candidates")
    fact_visit = data.get("fact_visit")
    fact_activity = data.get("fact_activity")
    timeline_path = data.get("timeline_path")

    candidates_count = _insert_if_new(
        engine,
        "dim_candidates",
        candidates,
        unique_columns=["candidate_id"],
    )

    fact_visit_count = _insert_if_new(
        engine,
        "fact_visit",
        fact_visit,
    ) if fact_visit is not None else 0

    fact_activity_count = _insert_if_new(
        engine,
        "fact_activity",
        fact_activity,
    ) if fact_activity is not None else 0

    timeline_count = _insert_if_new(
        engine,
        "timeline_path",
        timeline_path,
    ) if timeline_path is not None else 0

    return {
        "dim_candidates": candidates_count,
        "fact_visit": fact_visit_count,
        "fact_activity": fact_activity_count,
        "timeline_path": timeline_count,
    }
