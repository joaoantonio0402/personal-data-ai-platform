from pathlib import Path
import sys
import logging
import time

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.context_load import load_context_events
from src.analytics.context_matching import match_listenings_to_google_context
from src.database.connection import connect_to_database
from src.database.create_tables import create_tables

logger = logging.getLogger(__name__)


def main(tolerance_minutes=15):
    """Build idempotent Spotify-to-Google temporal relationships."""
    started_at = time.perf_counter()
    logger.info(
        "Context pipeline started | tolerance_minutes=%s",
        tolerance_minutes,
    )
    logger.info("Context pipeline creating/verifying tables")
    create_tables()
    logger.info("Context pipeline tables ready")
    engine = connect_to_database()
    logger.info("Context pipeline database connection ready")
    logger.info("Context pipeline matching listening events to Google context")
    events = match_listenings_to_google_context(
        engine,
        tolerance_minutes=tolerance_minutes,
    )
    logger.info(
        "Context pipeline matching finished | matched_events=%s",
        len(events),
    )
    logger.info("Context pipeline loading new relationships")
    inserted = load_context_events(events, engine)
    result = {
        "matched_events": len(events),
        "inserted_events": inserted,
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
