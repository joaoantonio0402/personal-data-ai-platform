import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import select, update

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database
from src.database.schema import Candidates, EnrichmentQueue


load_dotenv()
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def get_place_details(place_id):
	"""Return the Google name and Maps URL for a Place ID."""
	logger.info("Google Places request | place_id=%s", place_id)
	response = requests.get(
		f"https://places.googleapis.com/v1/places/{place_id}",
		headers={
			"Content-Type": "application/json",
			"X-Goog-Api-Key": GOOGLE_API_KEY,
			"X-Goog-FieldMask": "id,displayName,googleMapsUri",
		},
		timeout=10,
	)

	if response.status_code == 404:
		logger.warning("Google Place ID not found | place_id=%s", place_id)
		return None, None

	response.raise_for_status()
	data = response.json()
	name = data.get("displayName", {}).get("text")
	maps_url = data.get("googleMapsUri")
	logger.info(
		"Google Places response | place_id=%s | name=%s | has_maps_url=%s",
		place_id,
		name,
		bool(maps_url),
	)
	return name, maps_url


def get_data_to_enrich_from_db(reprocess_failed=False):
	"""Load only Google candidates currently waiting in the enrichment queue."""
	logger.info(
		"Loading Google enrichment queue | reprocess_failed=%s",
		reprocess_failed,
	)
	engine = connect_to_database()
	statuses = ["pending", "failed"] if reprocess_failed else ["pending"]

	with engine.connect() as connection:
		queue_df = pd.read_sql(
			select(EnrichmentQueue.enrichment_name).where(
				EnrichmentQueue.type == "candidate",
				EnrichmentQueue.method == "google",
				EnrichmentQueue.status.in_(statuses),
			),
			connection,
		)
		candidates_df = pd.read_sql(
			select(
				Candidates.candidate_id,
				Candidates.latitude,
				Candidates.longitude,
			),
			connection,
		)

	if queue_df.empty or candidates_df.empty:
		logger.info(
			"Google enrichment queue empty | queue_rows=%s | candidate_rows=%s",
			len(queue_df),
			len(candidates_df),
		)
		return candidates_df.iloc[0:0].copy()

	pending_ids = set(queue_df["enrichment_name"].astype(str))
	result = candidates_df[
		candidates_df["candidate_id"].astype(str).isin(pending_ids)
	].drop_duplicates(subset=["candidate_id"]).reset_index(drop=True)
	logger.info(
		"Google enrichment input loaded | queued=%s | candidates_to_process=%s",
		len(queue_df),
		len(result),
	)
	return result


def _maps_urls(place_id, latitude, longitude):
	coords_url = (
		"https://www.google.com/maps/search/?api=1"
		f"&query={latitude},{longitude}"
	)
	place_url = (
		"https://www.google.com/maps/search/?api=1"
		"&query=Google"
		f"&query_place_id={place_id}"
	)
	return coords_url, place_url


def _enrich_batch(candidates_df):
	"""Enrich and persist one batch in a single database transaction."""
	if candidates_df is None or candidates_df.empty:
		logger.info("Google enrichment batch skipped | reason=empty batch")
		return candidates_df
	if not GOOGLE_API_KEY:
		logger.error("Google enrichment cannot start | reason=missing API key")
		raise ValueError("GOOGLE_MAPS_API_KEY não encontrada no arquivo .env")

	engine = connect_to_database()
	processed_at = datetime.now(timezone.utc)
	results = []
	logger.info("Starting Google enrichment batch | size=%s", len(candidates_df))

	with engine.begin() as connection:
		for position, (_, row) in enumerate(candidates_df.iterrows(), start=1):
			place_id = row["candidate_id"]
			logger.info(
				"Google candidate %s/%s | place_id=%s",
				position,
				len(candidates_df),
				place_id,
			)
			try:
				name, google_maps_url = get_place_details(place_id)
				coords_url, place_url = _maps_urls(
					place_id, row["latitude"], row["longitude"]
				)
				connection.execute(
					update(Candidates)
					.where(Candidates.candidate_id == place_id)
					.values(
						url_google_maps_id=place_url,
						url_google_maps_coord=coords_url,
						name=name,
					)
				)
				connection.execute(
					update(EnrichmentQueue)
					.where(
						EnrichmentQueue.enrichment_name == place_id,
						EnrichmentQueue.type == "candidate",
						EnrichmentQueue.method == "google",
						EnrichmentQueue.status.in_(["pending", "failed"]),
					)
					.values(
						status="completed",
						enriched_at=processed_at,
						info=google_maps_url,
					)
				)
				results.append(True)
				logger.info(
					"Google candidate completed | place_id=%s | name=%s",
					place_id,
					name,
				)
			except Exception as error:
				logger.exception(
					"Google candidate failed | place_id=%s | error=%s",
					place_id,
					error,
				)
				connection.execute(
					update(EnrichmentQueue)
					.where(
						EnrichmentQueue.enrichment_name == place_id,
						EnrichmentQueue.type == "candidate",
						EnrichmentQueue.method == "google",
						EnrichmentQueue.status.in_(["pending", "failed"]),
					)
					.values(
						status="failed",
						enriched_at=processed_at,
						info=str(error),
					)
				)
				results.append(False)

	enriched = candidates_df.copy()
	enriched["google_enrichment_succeeded"] = results
	logger.info(
		"Google enrichment batch completed | processed=%s | succeeded=%s | failed=%s",
		len(enriched),
		int(enriched["google_enrichment_succeeded"].sum()),
		int((~enriched["google_enrichment_succeeded"]).sum()),
	)
	return enriched


def enrich_data(reprocess_failed=False, chunk_size=100):
	"""Process queued Google candidates in batches."""
	if chunk_size <= 0:
		logger.error("Invalid Google enrichment chunk size | chunk_size=%s", chunk_size)
		raise ValueError("chunk_size must be greater than zero")

	logger.info(
		"Starting Google enrichment pipeline | reprocess_failed=%s | chunk_size=%s",
		reprocess_failed,
		chunk_size,
	)
	candidates_df = get_data_to_enrich_from_db(reprocess_failed=reprocess_failed)
	summaries = []
	total_candidates = len(candidates_df)
	for batch_number, start in enumerate(range(0, total_candidates, chunk_size), start=1):
		batch = candidates_df.iloc[start:start + chunk_size].copy()
		logger.info(
			"Processing Google enrichment batch %s | rows=%s-%s",
			batch_number,
			start + 1,
			start + len(batch),
		)
		enriched = _enrich_batch(batch)
		summaries.append({
			"processed": len(enriched),
			"succeeded": int(enriched["google_enrichment_succeeded"].sum()),
			"failed": int((~enriched["google_enrichment_succeeded"]).sum()),
		})
	logger.info(
		"Google enrichment pipeline completed | candidates=%s | batches=%s",
		total_candidates,
		len(summaries),
	)
	return summaries


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	enrich_data(chunk_size=100)
