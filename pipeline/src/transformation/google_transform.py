from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_GOOGLE_DIR = PROJECT_ROOT / "data" / "processed" / "google"


def _safe_split_geo(value: pd.Series) -> pd.DataFrame:
    return (
        value.astype(str)
        .str.replace("geo:", "", regex=False)
        .str.split(",", n=1, expand=True)
    )


def transform_google_timeline(df: pd.DataFrame) -> dict:
    """Transform the raw Google timeline dataframe into visit, activity and path tables."""
    if df.empty:
        raise ValueError("The Google Timeline dataframe is empty.")

    mask_visit = ~(df["visit"].isna()) & (df["activity"].isna()) & (df["timelinePath"].isna())
    df_visit = df[mask_visit][["startTime", "endTime", "visit"]].copy()

    mask_activity = (df["visit"].isna()) & ~(df["activity"].isna()) & (df["timelinePath"].isna())
    df_activity = df[mask_activity][["startTime", "endTime", "activity"]].copy()

    mask_timeline = (df["visit"].isna()) & (df["activity"].isna()) & ~(df["timelinePath"].isna())
    df_timeline = df[mask_timeline][["startTime", "endTime", "timelinePath"]].copy()

    visit_df = pd.json_normalize(df_visit["visit"])
    df_visit = pd.concat([df_visit.drop(columns=["visit"]).reset_index(drop=True), visit_df.reset_index(drop=True)], axis=1)

    geo_cols = _safe_split_geo(df_visit["topCandidate.placeLocation"])
    df_visit[["topCandidate.latitude", "topCandidate.longitude"]] = geo_cols
    df_visit["topCandidate.latitude"] = pd.to_numeric(df_visit["topCandidate.latitude"], errors="coerce")
    df_visit["topCandidate.longitude"] = pd.to_numeric(df_visit["topCandidate.longitude"], errors="coerce")
    df_visit = df_visit.drop(columns=["topCandidate.placeLocation"], errors="ignore")

    activity_df = pd.json_normalize(df_activity["activity"])
    df_activity = pd.concat([
        df_activity.drop(columns=["activity"]).reset_index(drop=True),
        activity_df.reset_index(drop=True),
    ], axis=1)

    start_geo = _safe_split_geo(df_activity["start"])
    end_geo = _safe_split_geo(df_activity["end"])
    df_activity[["start_latitude", "start_longitude"]] = start_geo
    df_activity[["end_latitude", "end_longitude"]] = end_geo

    for col in ["start_latitude", "start_longitude", "end_latitude", "end_longitude"]:
        df_activity[col] = pd.to_numeric(df_activity[col], errors="coerce")

    df_activity["distanceMeters"] = pd.to_numeric(df_activity["distanceMeters"], errors="coerce")
    df_activity = df_activity.rename(columns={
        "startTime": "start_time",
        "endTime": "end_time",
        "distanceMeters": "distance_meters",
        "topCandidate.type": "activity_type",
        "topCandidate.probability": "activity_probability",
    })
    df_activity = df_activity.drop(columns=["start", "end", "probability"], errors="ignore")

    timeline_df = df_timeline.copy()
    # A raw timeline path is not guaranteed to match a fact_activity row in a 1:1 way.
    # Keep the field for compatibility but avoid creating invalid foreign keys.
    timeline_df["activity_id"] = None
    timeline_df = timeline_df.explode("timelinePath").reset_index(drop=True)
    timeline_df = pd.concat([
        timeline_df.drop(columns=["timelinePath"]).reset_index(drop=True),
        pd.json_normalize(timeline_df["timelinePath"]).reset_index(drop=True),
    ], axis=1)

    timeline_df[["latitude", "longitude"]] = _safe_split_geo(timeline_df["point"])
    timeline_df["latitude"] = pd.to_numeric(timeline_df["latitude"], errors="coerce")
    timeline_df["longitude"] = pd.to_numeric(timeline_df["longitude"], errors="coerce")
    timeline_df["duration_minutes_offset"] = pd.to_numeric(
        timeline_df["durationMinutesOffsetFromStartTime"], errors="coerce"
    ).astype("Int64")
    timeline_df = timeline_df.drop(columns=["point", "durationMinutesOffsetFromStartTime"], errors="ignore")
    timeline_df = timeline_df.rename(columns={
        "startTime": "start_time",
        "endTime": "end_time",
    })
    timeline_df = timeline_df.reset_index(drop=True)

    df_visit_base = df_visit.rename(columns={
        "startTime": "start_time",
        "endTime": "end_time",
        "topCandidate.placeID": "candidate_id",
        "topCandidate.semanticType": "semantic_type",
        "topCandidate.latitude": "latitude",
        "topCandidate.longitude": "longitude",
        "topCandidate.probability": "candidate_probability",
        "probability": "probability",
    })

    df_candidates = (
        df_visit_base[
            ["candidate_id", "semantic_type", "latitude", "longitude"]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    df_visit_fact = df_visit_base[
        ["start_time", "end_time", "candidate_id", "probability", "candidate_probability"]
    ].copy()
    df_visit_fact["duration_minutes"] = (
        (df_visit_fact["end_time"] - df_visit_fact["start_time"]).dt.total_seconds() / 60
    ).astype(float)
    df_visit_fact = df_visit_fact[[
        "start_time",
        "end_time",
        "duration_minutes",
        "candidate_id",
        "probability",
        "candidate_probability",
    ]]

    PROCESSED_GOOGLE_DIR.mkdir(parents=True, exist_ok=True)
    df_candidates.to_csv(PROCESSED_GOOGLE_DIR / "dim_candidates.csv", index=False)
    df_visit_fact.to_csv(PROCESSED_GOOGLE_DIR / "fact_visit.csv", index=False)
    df_activity.to_csv(PROCESSED_GOOGLE_DIR / "fact_activity.csv", index=False)
    timeline_df.to_csv(PROCESSED_GOOGLE_DIR / "timeline_path.csv", index=False)

    return {
        "candidates": df_candidates,
        "fact_visit": df_visit_fact,
        "fact_activity": df_activity,
        "timeline_path": timeline_df,
    }
