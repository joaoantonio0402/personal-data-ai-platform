from pathlib import Path
import sys
import pandas as pd
from sqlalchemy import and_, select
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import connect_to_database
from src.database.schema import Base, DimAlbum, DimArtist, DimTrack, FactListening
project_root = Path(__file__).resolve().parents[2]

new_records_dir = (
        project_root
        / "data"
        / "processed"
        / "spotify"
    )

# dim_artists_df = pd.read_csv(new_records_dir / "new_artists_enriched.csv")
# dim_albums_df = pd.read_csv(new_records_dir / "new_albums_enriched.csv").drop("artist_name", axis=1)
# dim_tracks_df = pd.read_csv(new_records_dir / "new_tracks_enriched.csv").drop("artist_name", axis=1)
# fact_listening_df = pd.read_csv(new_records_dir / "new_streams.csv")


def _upsert_dimension(dataframe, model, key_columns):
    columns = [column.name for column in model.__table__.columns]
    dataframe = dataframe.drop_duplicates(subset=key_columns).copy()
    dataframe = dataframe[[column for column in columns if column in dataframe]]

    if dataframe.empty:
        return dataframe

    engine = connect_to_database()
    primary_key = model.__table__.primary_key.columns[0]
    rows = dataframe.where(pd.notna(dataframe), None).to_dict(orient="records")

    with engine.begin() as connection:
        for row in rows:
            filters = [getattr(model, column) == row[column] for column in key_columns]
            existing_id = connection.execute(
                select(primary_key).where(and_(*filters))
            ).scalar_one_or_none()

            if existing_id is None:
                connection.execute(model.__table__.insert().values(**row))
            else:
                values = {
                    column: value
                    for column, value in row.items()
                    if column != primary_key.name and column not in key_columns
                }
                if values:
                    connection.execute(
                        model.__table__.update()
                        .where(primary_key == existing_id)
                        .values(**values)
                    )

    return dataframe


def load_enriched_data(fact_listening: pd.DataFrame, dim: dict):
    """Load enriched dimensions and listening facts into the database."""
    required_dimensions = {"artist", "album", "track"}
    missing_dimensions = required_dimensions - dim.keys()
    if missing_dimensions:
        raise ValueError(
            f"Missing dimensions: {', '.join(sorted(missing_dimensions))}"
        )

    engine = connect_to_database()
    Base.metadata.create_all(engine)

    artists = dim["artist"].copy()
    albums = dim["album"].copy()
    tracks = dim["track"].copy()

    artist_columns = [column.name for column in DimArtist.__table__.columns]
    artist_columns.remove("artist_id")
    artists = artists[[column for column in artist_columns if column in artists]]
    _upsert_dimension(artists, DimArtist, ["artist_name"])

    with engine.connect() as connection:
        artist_ids = pd.read_sql(
            select(DimArtist.artist_id, DimArtist.artist_name),
            connection,
        )

    albums = albums.merge(artist_ids, on="artist_name", how="inner")
    album_columns = [column.name for column in DimAlbum.__table__.columns]
    album_columns.remove("album_id")
    albums = albums[[column for column in album_columns if column in albums]]
    _upsert_dimension(albums, DimAlbum, ["album_name", "artist_id"])

    with engine.connect() as connection:
        album_ids = pd.read_sql(
            select(DimAlbum.album_id, DimAlbum.album_name, DimAlbum.artist_id),
            connection,
        )

    tracks = tracks.merge(
        artist_ids,
        on="artist_name",
        how="inner",
        suffixes=("", "_artist"),
    )
    tracks = tracks.merge(
        album_ids[["album_id", "album_name", "artist_id"]],
        on=["album_name", "artist_id"],
        how="inner",
        suffixes=("", "_album"),
    )
    track_columns = [column.name for column in DimTrack.__table__.columns]
    track_columns.remove("track_id")
    tracks = tracks[[column for column in track_columns if column in tracks]]
    tracks = tracks.drop(
        columns=["spotify_featured_artists"],
        errors="ignore"
    )
    _upsert_dimension(
        tracks,
        DimTrack,
        ["track_name", "artist_id", "album_id"],
    )

    with engine.connect() as connection:
        track_ids = pd.read_sql(
            select(DimTrack.track_id, DimTrack.track_name, DimTrack.artist_name),
            connection,
        )

    facts = fact_listening.merge(
        track_ids,
        on=["track_name", "artist_name"],
        how="inner",
    )
    fact_columns = [column.name for column in FactListening.__table__.columns]
    fact_columns.remove("listening_id")
    facts = facts[[column for column in fact_columns if column in facts]]
    facts.to_sql(FactListening.__tablename__, con=engine, if_exists="append", index=False)

    return {
        "artists": len(artists),
        "albums": len(albums),
        "tracks": len(tracks),
        "facts": len(facts),
    }



