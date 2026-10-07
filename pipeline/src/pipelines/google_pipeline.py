from pathlib import Path
import sys
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.google_extract import extract_google_timeline
from src.transformation.google_transform import transform_google_timeline
from src.staging.google_stage import stage_google_data
from src.load.google_load import load_google_data
from src.database.create_tables import create_tables
from src.control.enrichment_control import control_enrichment_queue
from src.enrichment.google_enrich import enrich_data


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Google pipeline")
    create_tables()
    raw_df = extract_google_timeline()
    logger.info("Google timeline extracted | rows=%s", len(raw_df))
    summary = {
        "dim_candidates": 0,
        "fact_visit": 0,
        "fact_activity": 0,
        "timeline_path": 0,
    }
    if not raw_df.empty:
        transformed = transform_google_timeline(raw_df)
        staged = stage_google_data(transformed)
        summary = load_google_data(staged)
        logger.info("Google timeline loaded | summary=%s", summary)
    else:
        logger.info("No new Google timeline data; processing pending enrichment queue")
    control_enrichment_queue()
    summary["google_enrichment"] = enrich_data(chunk_size=10, reprocess_failed=True)
    logger.info("Google pipeline completed | summary=%s", summary)
    return summary


if __name__ == "__main__":
    result = main()
    print(result)
