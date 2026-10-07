from __future__ import annotations

import logging
from pathlib import Path
import sys
import time

import pandas as pd
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.schema import (
    Candidates,
    DimTrack,
    FactActivity,
    FactListening,
    FactVisit,
    TimelinePath,
)

logger = logging.getLogger(__name__)


def _google_maps_url(latitude, longitude):
    if pd.isna(latitude) or pd.isna(longitude):
        return None
    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"

EVENT_COLUMNS = [
    "timestamp",
    "listening_id",
    "track_name",
    "context_type",
    "visit_id",
    "activity_id",
    "match_method",
    "match_score",
    "time_distance_seconds",
    "overlap_seconds",
    "latitude",
    "longitude",
    "start_latitude",
    "start_longitude",
    "end_latitude",
    "end_longitude",
    "location_source",
    "location_precision",
    "google_maps_url",
]


def _empty_events():
    return pd.DataFrame(columns=EVENT_COLUMNS)


def _load_source_data(engine, listening_ids=None):
    started_at = time.perf_counter()
    logger.info("Loading context sources from database")
    with engine.connect() as connection:
        listening_query = select(
            FactListening.listening_id,
            FactListening.timestamp_utc,
            DimTrack.track_name,
        ).join(
            DimTrack,
            FactListening.track_id == DimTrack.track_id,
            isouter=True,
        )
        if listening_ids is not None:
            listening_query = listening_query.where(
                FactListening.listening_id.in_(listening_ids)
            )
        listenings = pd.read_sql(listening_query, connection)
        visits = pd.read_sql(
            select(
                FactVisit.visit_id,
                FactVisit.start_time,
                FactVisit.end_time,
                FactVisit.candidate_id,
                Candidates.latitude,
                Candidates.longitude,
            ).join(
                Candidates,
                FactVisit.candidate_id == Candidates.candidate_id,
                isouter=True,
            ),
            connection,
        )
        activities = pd.read_sql(
            select(
                FactActivity.activity_id,
                FactActivity.start_time,
                FactActivity.end_time,
                FactActivity.start_latitude,
                FactActivity.start_longitude,
                FactActivity.end_latitude,
                FactActivity.end_longitude,
            ),
            connection,
        )
        timeline_path = pd.read_sql(
            select(
                TimelinePath.start_time,
                TimelinePath.end_time,
                TimelinePath.latitude,
                TimelinePath.longitude,
                TimelinePath.duration_minutes_offset,
            ),
            connection,
        )

    listenings["timestamp_utc"] = pd.to_datetime(
        listenings["timestamp_utc"], errors="coerce", utc=True
    )
    for frame in (visits, activities):
        frame["start_time"] = pd.to_datetime(
            frame["start_time"], errors="coerce", utc=True
        )
        frame["end_time"] = pd.to_datetime(
            frame["end_time"], errors="coerce", utc=True
        )
    timeline_path["start_time"] = pd.to_datetime(
        timeline_path["start_time"], errors="coerce", utc=True
    )
    timeline_path["end_time"] = pd.to_datetime(
        timeline_path["end_time"], errors="coerce", utc=True
    )

    activities["_path_points"] = [
        _path_points_for_activity(row, timeline_path)
        for row in activities.itertuples(index=False)
    ]

    logger.info(
        "Context sources loaded | listenings=%s | visits=%s | activities=%s | elapsed_seconds=%.2f",
        len(listenings),
        len(visits),
        len(activities),
        time.perf_counter() - started_at,
    )
    return listenings, visits, activities


def _path_points_for_activity(activity, timeline_path):
    if timeline_path.empty:
        return []

    valid = timeline_path.dropna(
        subset=["start_time", "end_time", "latitude", "longitude"]
    )
    overlaps = valid.loc[
        (valid["start_time"] <= activity.end_time)
        & (valid["end_time"] >= activity.start_time)
    ].copy()
    if overlaps.empty:
        return []

    overlaps["point_time"] = overlaps["start_time"] + pd.to_timedelta(
        overlaps["duration_minutes_offset"].fillna(0), unit="m"
    )
    return overlaps[
        ["point_time", "latitude", "longitude"]
    ].sort_values("point_time").to_dict("records")


def _match_context(listenings, contexts, context_type, tolerance_seconds):
    if listenings.empty or contexts.empty:
        logger.info(
            "Context matching skipped | type=%s | listenings=%s | contexts=%s",
            context_type,
            len(listenings),
            len(contexts),
        )
        return []

    started_at = time.perf_counter()
    id_column = "visit_id" if context_type == "visit" else "activity_id"
    matches = []
    valid_contexts = contexts.dropna(
        subset=["start_time", "end_time", id_column]
    )
    logger.info(
        "Context matching started | type=%s | listenings=%s | contexts=%s | valid_contexts=%s | tolerance_seconds=%s",
        context_type,
        len(listenings),
        len(contexts),
        len(valid_contexts),
        tolerance_seconds,
    )

    for position, listening in enumerate(
        listenings.itertuples(index=False),
        start=1,
    ):
        timestamp = listening.timestamp_utc
        if pd.isna(timestamp):
            continue

        starts = valid_contexts["start_time"]
        ends = valid_contexts["end_time"]
        inside = (starts <= timestamp) & (timestamp <= ends)
        distance = pd.concat(
            [
                (timestamp - starts).abs(),
                (timestamp - ends).abs(),
            ],
            axis=1,
        ).min(axis=1)
        eligible = inside | (distance <= pd.Timedelta(seconds=tolerance_seconds))

        for context_index, context in valid_contexts.loc[eligible].iterrows():
            context_start = context.start_time
            context_end = context.end_time
            context_distance = 0 if inside.loc[context_index] else int(
                distance.loc[context_index].total_seconds()
            )
            score = 1.0 if context_distance == 0 else max(
                0.0,
                1.0 - (context_distance / tolerance_seconds),
            )
            if context_type == "visit":
                latitude = context.get("latitude")
                longitude = context.get("longitude")
                start_latitude = latitude
                start_longitude = longitude
                end_latitude = latitude
                end_longitude = longitude
                location_source = "dim_candidates"
                location_precision = "approximate"
            else:
                path_points = context.get("_path_points", [])
                if path_points:
                    nearest = min(
                        path_points,
                        key=lambda point: abs(point["point_time"] - timestamp),
                    )
                    latitude = nearest["latitude"]
                    longitude = nearest["longitude"]
                    start_latitude = path_points[0]["latitude"]
                    start_longitude = path_points[0]["longitude"]
                    end_latitude = path_points[-1]["latitude"]
                    end_longitude = path_points[-1]["longitude"]
                    location_source = "timeline_path"
                    location_precision = "approximate"
                else:
                    latitude = context.get("start_latitude")
                    longitude = context.get("start_longitude")
                    start_latitude = context.get("start_latitude")
                    start_longitude = context.get("start_longitude")
                    end_latitude = context.get("end_latitude")
                    end_longitude = context.get("end_longitude")
                    location_source = "fact_activity"
                    location_precision = "approximate"
            matches.append(
                {
                    "timestamp": timestamp,
                    "listening_id": listening.listening_id,
                    "track_name": listening.track_name,
                    "context_type": context_type,
                    "visit_id": context.get("visit_id"),
                    "activity_id": context.get("activity_id"),
                    "match_method": (
                        "temporal_overlap"
                        if context_distance == 0
                        else "temporal_proximity"
                    ),
                    "match_score": score,
                    "time_distance_seconds": context_distance,
                    "overlap_seconds": 0 if context_start <= timestamp <= context_end else None,
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_latitude": start_latitude,
                    "start_longitude": start_longitude,
                    "end_latitude": end_latitude,
                    "end_longitude": end_longitude,
                    "location_source": location_source,
                    "location_precision": location_precision,
                    "google_maps_url": _google_maps_url(latitude, longitude),
                }
            )

        if position % 1000 == 0:
            logger.info(
                "Context matching progress | type=%s | processed=%s/%s | matches=%s | elapsed_seconds=%.2f",
                context_type,
                position,
                len(listenings),
                len(matches),
                time.perf_counter() - started_at,
            )

    logger.info(
        "Context matching finished | type=%s | processed=%s | matches=%s | elapsed_seconds=%.2f",
        context_type,
        len(listenings),
        len(matches),
        time.perf_counter() - started_at,
    )
    return matches


def match_listenings_to_google_context(
    engine,
    tolerance_minutes=15,
    listening_ids=None,
):
    """Find Google visits and activities that contain or border each listening."""
    if tolerance_minutes < 0:
        raise ValueError("tolerance_minutes must be non-negative")

    listenings, visits, activities = _load_source_data(
        engine,
        listening_ids=listening_ids,
    )
    tolerance_seconds = tolerance_minutes * 60
    matches = _match_context(
        listenings,
        visits,
        "visit",
        tolerance_seconds,
    )
    matches.extend(
        _match_context(
            listenings,
            activities,
            "activity",
            tolerance_seconds,
        )
    )

    if not matches:
        return _empty_events()

    events = pd.DataFrame(matches, columns=EVENT_COLUMNS)
    events["_location_available"] = events[[
        "latitude",
        "longitude",
    ]].notna().all(axis=1)
    events["_context_priority"] = events["context_type"].map(
        {"visit": 0, "activity": 1}
    ).fillna(9)
    events = events.sort_values(
        [
            "listening_id",
            "_location_available",
            "match_score",
            "time_distance_seconds",
            "_context_priority",
        ],
        ascending=[True, False, False, True, True],
        kind="stable",
    )
    selected = events.drop_duplicates(
        subset=["listening_id"],
        keep="first",
    )
    return selected[EVENT_COLUMNS].reset_index(drop=True)
