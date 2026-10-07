from pathlib import Path
import sys
import logging
import time

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.context_load import (
    get_pending_context_listenings,
    load_context_events,
    mark_context_listenings,
    queue_new_context_listenings,
)
from src.analytics.context_matching import match_listenings_to_google_context
from src.database.connection import connect_to_database
from src.database.create_tables import create_tables

logger = logging.getLogger(__name__)


def main(tolerance_minutes=15, reprocess_failed=True, chunk_size=10):
    """Process only context queue rows that are waiting for matching."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    started_at = time.perf_counter()
    logger.info(
        "Context pipeline started | tolerance_minutes=%s | chunk_size=%s | reprocess_failed=%s",
        tolerance_minutes,
        chunk_size,
        reprocess_failed,
    )
    logger.info("Context pipeline creating/verifying tables")
    create_tables()
    logger.info("Context pipeline tables ready")
    engine = connect_to_database()
    logger.info("Context pipeline database connection ready")
    queued = queue_new_context_listenings(engine)
    pending_ids = get_pending_context_listenings(
        engine,
        reprocess_failed=reprocess_failed,
    )
    logger.info(
        "Context queue ready | queued_new=%s | pending=%s",
        queued,
        len(pending_ids),
    )
    if not pending_ids:
        return {
            "queued_new": queued,
            "pending": 0,
            "matched_events": 0,
            "inserted_events": 0,
        }
    total_matched = 0
    total_inserted = 0
    failed_batches = 0
    total_batches = (len(pending_ids) + chunk_size - 1) // chunk_size

    for batch_number, start in enumerate(
        range(0, len(pending_ids), chunk_size),
        start=1,
    ):
        batch_ids = pending_ids[start:start + chunk_size]
        logger.info(
            "Processing context batch %s/%s | rows=%s-%s/%s",
            batch_number,
            total_batches,
            start + 1,
            start + len(batch_ids),
            len(pending_ids),
        )
        try:
            events = match_listenings_to_google_context(
                engine,
                tolerance_minutes=tolerance_minutes,
                listening_ids=batch_ids,
            )
            inserted = load_context_events(events, engine)
            mark_context_listenings(engine, batch_ids, "completed")
            total_matched += len(events)
            total_inserted += inserted
            logger.info(
                "Context batch completed %s/%s | matched=%s | inserted=%s",
                batch_number,
                total_batches,
                len(events),
                inserted,
            )
        except Exception as error:
            failed_batches += 1
            mark_context_listenings(engine, batch_ids, "failed", str(error))
            logger.exception(
                "Context batch failed %s/%s | rows=%s | error=%s",
                batch_number,
                total_batches,
                len(batch_ids),
                error,
            )
    logger.info(
        "Context pipeline matching finished | matched_events=%s | failed_batches=%s",
        total_matched,
        failed_batches,
    )
    result = {
        "queued_new": queued,
        "pending": len(pending_ids),
        "matched_events": total_matched,
        "inserted_events": total_inserted,
        "failed_batches": failed_batches,
    }
    logger.info(
        "Context pipeline finished | result=%s | elapsed_seconds=%.2f",
        result,
        time.perf_counter() - started_at,
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    print(main())
