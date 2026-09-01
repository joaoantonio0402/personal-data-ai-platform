# Google + Spotify Personal Intelligence Platform

This project combines music consumption data, enriched metadata, and machine learning to understand listening patterns and support personalized recommendations. The repository is organized around three main pillars:

1. Pipeline
2. ML Models
3. AI Agent

---

## 1. Pipeline

The pipeline is responsible for ingesting, transforming, enriching, and loading data from multiple sources into a normalized database model.

### Main responsibilities
- Extract music listening data from Last.fm and related sources
- Process and normalize raw records
- Merge Spotify metadata and audio features
- Build a star-schema style data model for analytics and ML
- Enrich entities such as artists, albums, and tracks
- Keep a queue of pending enrichments and mark them as completed or failed

### Data flow
- Raw ingestion: collects listening events and source metadata
- Transformation: cleans and standardizes fields like track, artist, album, timestamps, and URLs
- Staging: loads raw streams into staging tables
- Dimensions: builds artist, album, and track dimension tables
- Enrichment: queries Spotify and other providers for metadata and audio features
- Facts: stores listening events in the fact table for downstream analysis

### Typical architecture
- `pipeline/src/extraction`: data extraction logic
- `pipeline/src/transformation`: raw-to-structured transformations
- `pipeline/src/staging`: data staging and validation
- `pipeline/src/load`: inserts into database tables
- `pipeline/src/control`: orchestration of enrichment queue
- `pipeline/src/enrichment`: Spotify/ReccoBeats enrichment logic
- `pipeline/src/database`: schema and database connection management

### Database model
The system stores both business entities and listening events, including:
- `dim_artist`
- `dim_album`
- `dim_track`
- `track_audio_features`
- `fact_listening`
- `enrichment_queue`

This enables both analytical queries and model training using consistent identifiers such as `track_id` and `artist_id`.

---

## 2. ML Models

The ML layer is focused on predicting user preference signals from audio features and listening behavior.

### Goal
Create models that estimate the likelihood that a user will like a song based on its musical profile and historical behavior.

### Training data
The model uses a dataset composed of:
- `track_id`
- `artist_name`
- `quantidade_streams`
- audio features such as:
  - `danceability`
  - `energy`
  - `valence`
  - `tempo`
  - `acousticness`
  - `instrumentalness`
  - `liveness`
  - `loudness`
  - `speechiness`
  - `popularity`
  - `key`
  - `mode`

This creates a supervised learning dataset where the target is a preference signal such as whether the user interacted with a track or listened to it enough to count as a positive signal.

### Current notebook workflow
The experiments and prototype modelling live in the `ml-model` directory, where notebooks and exploratory scripts are used to:
- join listening facts with track metadata
- build training tables with audio features
- test classification models
- evaluate recommendation quality and predictive power

### Example model intent
The project is designed to support models such as:
- Logistic Regression
- Random Forest
- XGBoost
- CatBoost
- Gradient boosting models

These models can learn patterns from a user’s listening history and predict whether a track is likely to be enjoyable given its audio characteristics.

---

## 3. AI Agent

The AI agent layer is the intelligent interface on top of the data and models. It is designed to turn raw listening data into personalized recommendations and conversational decision support.

### Responsibilities
- interpret user preferences and listening history
- explain why a track may match a user profile
- combine structured data from the database with model outputs
- recommend music based on audio features, genres, artists, and listening patterns
- provide a natural-language interface for personalization and music discovery

### Design direction
The agent can act as a recommendation layer that uses:
- historical interactions from `fact_listening`
- enriched metadata from Spotify
- model predictions from the ML component
- user context such as favorite artists, music mood, or listening time patterns

In practical terms, the AI agent may answer questions like:
- “Which songs should I listen to next?”
- “Why is this song recommended to me?”
- “What sound profile aligns with my recent listening behavior?”

This turns the project from a data pipeline into an intelligent recommendation system.

---

## Repository layout

```text
.
├── pipeline/
│   ├── src/
│   ├── data/
│   ├── notebooks/
│   └── tests/
├── ml-model/
│   └── notebooks and experiment files
├── .gitignore
├── README.md
└── .venv/
```

---

## Getting started

### Requirements
- Python 3.10+
- PostgreSQL
- Spotify API credentials
- Last.fm API key

### Environment variables
Set up the following environment variables before running the pipeline:

```bash
LASTFM_API_KEY=your_lastfm_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

### Run the pipeline
From the project root:

```bash
cd pipeline
python src/pipelines/spt_pipeline.py
```

### Explore the ML notebooks
Open the notebooks under `ml-model/` to:
- inspect enriched datasets
- test joins between listening and track features
- prototype models and evaluate results

---

## Project vision

This repository brings together data engineering, recommendation modelling, and AI into one personalized music intelligence stack. The result is a system that can ingest listening behavior, enrich it with metadata and audio analysis, train models on user preference signals, and expose the outcome through an intelligent agent experience.

---

## License

This project is intended for research, experimentation, and personal music recommendation engineering. Add a license file if you plan to distribute it publicly or share it with other contributors.
