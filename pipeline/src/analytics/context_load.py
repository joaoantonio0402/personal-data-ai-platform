from __future__ import annotations

import logging
from pathlib import Path
import sys
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import exists, select, update

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.schema import Base, ContextQueue, FactContextEvent, FactListening

logger = logging.getLogger(__name__)

RELATIONSHIP_COLUMNS = ["listening_id", "visit_id", "activity_id"]


def queue_new_context_listenings(engine):
    """Queue listening rows that have never entered context processing."""
    logger.info("Context queue discovery started")
    Base.metadata.create_all(engine, tables=[ContextQueue.__table__])

    with engine.begin() as connection:
        new_listenings = connection.execute(
            select(FactListening.listening_id).where(
                ~exists().where(
                    ContextQueue.listening_id == FactListening.listening_id
                ),
                ~exists().where(
                    FactContextEvent.listening_id == FactListening.listening_id
                ),
            )
        ).scalars().all()

        if not new_listenings:
            logger.info("Context queue discovery finished | queued_new=0")
            return 0

        connection.execute(
            ContextQueue.__table__.insert(),
            [
                {
                    "listening_id": listening_id,
                    "status": "pending",
                    "attempts": 0,
                    "queued_at": datetime.now(timezone.utc),
                }
                for listening_id in new_listenings
            ],
        )
    logger.info(
        "Context queue discovery finished | queued_new=%s",
        len(new_listenings),
    )
    return len(new_listenings)


def get_pending_context_listenings(engine, reprocess_failed=False):
    statuses = ["pending", "failed"] if reprocess_failed else ["pending"]
    with engine.connect() as connection:
        pending = connection.execute(
            select(ContextQueue.listening_id)
            .where(ContextQueue.status.in_(statuses))
            .order_by(ContextQueue.listening_id)
        ).scalars().all()
    logger.info(
        "Context queue pending lookup finished | statuses=%s | pending=%s",
        statuses,
        len(pending),
    )
    return pending


def mark_context_listenings(engine, listening_ids, status, info=None):
    if not listening_ids:
        return 0

    with engine.begin() as connection:
        result = connection.execute(
            update(ContextQueue)
            .where(ContextQueue.listening_id.in_(listening_ids))
            .values(
                status=status,
                info=info,
                attempts=ContextQueue.attempts + 1,
                processed_at=datetime.now(timezone.utc),
            )
        )
    logger.info(
        "Context queue status updated | status=%s | rows=%s",
        status,
        result.rowcount,
    )
    return result.rowcount


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
    events = events.drop_duplicates(subset=["listening_id"])
    logger.info(
        "Context load deduplicated | unique_listenings=%s",
        len(events),
    )

    with engine.connect() as connection:
        existing = pd.read_sql(
            select(
                FactContextEvent.listening_id,
                FactContextEvent.visit_id,
                FactContextEvent.activity_id,
            ).where(FactContextEvent.listening_id.in_(
                events["listening_id"].dropna().tolist()
            )),
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
        chunksize=1000,
    )
    logger.info("Context load finished | inserted_events=%s", len(events))
    return len(events)
