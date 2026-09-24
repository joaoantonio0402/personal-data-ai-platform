from __future__ import annotations

import logging
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.schema import Base, FactContextEvent

logger = logging.getLogger(__name__)

RELATIONSHIP_COLUMNS = ["listening_id", "visit_id", "activity_id"]


def _relationship_keys(frame):
    normalized = frame[RELATIONSHIP_COLUMNS].copy()
    for column in RELATIONSHIP_COLUMNS:
        normalized[column] = normalized[column].astype("Int64")
    return pd.MultiIndex.from_frame(normalized)


def load_context_events(events, engine):
    """Insert new context relationships without creating duplicates."""
    if events is None or events.empty:
        logger.info("Context load skipped | no matched events")
        return 0

    logger.info("Context load started | matched_events=%s", len(events))
    Base.metadata.create_all(engine, tables=[FactContextEvent.__table__])
    events = events.copy()
    events = events.drop_duplicates(subset=RELATIONSHIP_COLUMNS)

    with engine.connect() as connection:
        existing = pd.read_sql(
            select(
                FactContextEvent.listening_id,
                FactContextEvent.visit_id,
                FactContextEvent.activity_id,
            ),
            connection,
        )

    if not existing.empty:
        logger.info("Context load existing relationships=%s", len(existing))
        events = events.loc[
            ~_relationship_keys(events).isin(_relationship_keys(existing))
        ].copy()

    if events.empty:
        logger.info("Context load finished | inserted_events=0")
        return 0

    events["created_at"] = pd.Timestamp.now(tz="UTC")
    columns = [column.name for column in FactContextEvent.__table__.columns]
    events = events[[column for column in columns if column in events]]
    events.to_sql(
        FactContextEvent.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
    )
    logger.info("Context load finished | inserted_events=%s", len(events))
    return len(events)
