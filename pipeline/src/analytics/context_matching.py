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

from src.database.schema import FactActivity, FactListening, FactVisit

logger = logging.getLogger(__name__)

EVENT_COLUMNS = [
    "timestamp",
    "listening_id",
    "visit_id",
    "activity_id",
    "match_method",
    "match_score",
    "time_distance_seconds",
    "overlap_seconds",
]


def _empty_events():
    return pd.DataFrame(columns=EVENT_COLUMNS)


def _load_source_data(engine):
    started_at = time.perf_counter()
    logger.info("Loading context sources from database")
    with engine.connect() as connection:
        listenings = pd.read_sql(
            select(
                FactListening.listening_id,
                FactListening.timestamp_utc,
            ),
            connection,
        )
        visits = pd.read_sql(
            select(
                FactVisit.visit_id,
                FactVisit.start_time,
                FactVisit.end_time,
            ),
            connection,
        )
        activities = pd.read_sql(
            select(
                FactActivity.activity_id,
                FactActivity.start_time,
                FactActivity.end_time,
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

    logger.info(
        "Context sources loaded | listenings=%s | visits=%s | activities=%s | elapsed_seconds=%.2f",
        len(listenings),
        len(visits),
        len(activities),
        time.perf_counter() - started_at,
    )
    return listenings, visits, activities


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
            matches.append(
                {
                    "timestamp": timestamp,
                    "listening_id": listening.listening_id,
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


def match_listenings_to_google_context(engine, tolerance_minutes=15):
    """Find Google visits and activities that contain or border each listening."""
    if tolerance_minutes < 0:
        raise ValueError("tolerance_minutes must be non-negative")

    listenings, visits, activities = _load_source_data(engine)
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
    return pd.DataFrame(matches, columns=EVENT_COLUMNS).drop_duplicates(
        subset=["listening_id", "visit_id", "activity_id"]
    ).reset_index(drop=True)
