from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Boolean
)

from sqlalchemy.orm import declarative_base


Base = declarative_base()


# ==========================
# Spotify
# ==========================

class DimArtist(Base):
    __tablename__ = "dim_artist"

    artist_id = Column(Integer, primary_key=True, autoincrement=True)
    
    artist_mbid = Column(String)
    spotify_artist_id = Column(String)  # Mapped from 'artist_id' in CSV
    artist_name = Column(String)
    spotify_artist_url = Column(String)
    spotify_followers = Column(Integer)
    spotify_popularity = Column(Integer)
    spotify_genres = Column(String)


class DimAlbum(Base):
    __tablename__ = "dim_album"

    album_id = Column(Integer, primary_key=True, autoincrement=True)
    artist_id = Column(Integer, ForeignKey("dim_artist.artist_id"), nullable=False)
    album_name = Column(String)
    
    album_mbid = Column(String)
    spotify_album_id = Column(String)  # Mapped from 'album_id' in CSV
    #spotify_album_name = Column(String)
    spotify_album_type = Column(String)
    spotify_total_tracks = Column(Integer)
    spotify_release_date = Column(String)      # String to accommodate precision variations
    spotify_release_date_precision = Column(String)
    spotify_album_url = Column(String)


class DimTrack(Base):
    __tablename__ = "dim_track"

    track_id = Column(Integer, primary_key=True, autoincrement=True)
    artist_id = Column(Integer, ForeignKey("dim_artist.artist_id"), nullable=False)
    album_id = Column(Integer, ForeignKey("dim_album.album_id"), nullable=False)
    track_name = Column(String)
    artist_name = Column(String)
    track_mbid = Column(String)
    spotify_track_id = Column(String)  # Mapped from 'track_id' in CSV
    spotify_isrc = Column(String)
    spotify_has_feat = Column(Boolean)
    spotify_artist_count = Column(Integer)
    spotify_featured_artists = Column(String)
    spotify_release_date = Column(String)
    spotify_duration_ms = Column(Integer)
    spotify_explicit = Column(Boolean)
    spotify_track_number = Column(Integer)
    spotify_disc_number = Column(Integer)
    spotify_popularity = Column(Integer)
    spotify_track_url = Column(String)
    recco_track_id = Column(String)


    # Melodata

    melodata_isrc = Column(String(20))

    melodata_title = Column(String(255))
    melodata_artist = Column(String(255))

    melodata_bpm = Column(Integer)
    melodata_key = Column(String(10))
    melodata_key_confidence = Column(Float)

    melodata_energy = Column(Float)
    melodata_danceability = Column(Float)
    melodata_valence = Column(Float)
    melodata_acousticness = Column(Float)
    melodata_loudness = Column(Float)
    melodata_instrumentalness = Column(Float)
    melodata_speechiness = Column(Float)
    melodata_liveness = Column(Float)

    melodata_time_signature = Column(Integer)

    melodata_analysis_version = Column(String(100))
    melodata_source = Column(String(100))
    
    # Enriched audio features from reccobeats
    reccobeats_id = Column(String(50))
    reccobeats_href = Column(String(255))
    reccobeats_isrc = Column(String(20))

    reccobeats_acousticness = Column(Float)
    reccobeats_danceability = Column(Float)
    reccobeats_energy = Column(Float)
    reccobeats_instrumentalness = Column(Float)

    reccobeats_key = Column(Integer)
    reccobeats_liveness = Column(Float)
    reccobeats_loudness = Column(Float)
    reccobeats_mode = Column(Integer)
    reccobeats_speechiness = Column(Float)
    reccobeats_tempo = Column(Float)
    reccobeats_valence = Column(Float)


class FactListening(Base):
    __tablename__ = "fact_listening"

    listening_id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("dim_track.track_id"), nullable=False)

    timestamp_utc = Column(DateTime, nullable=False)
    timestamp_uts = Column(Integer, nullable=False)
    track_url = Column(String)
    # streamable = Column(Integer)



# ==========================
# Google Timeline
# ==========================


class FactVisit(Base):
    __tablename__ = "fact_visit"


    visit_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    start_time = Column(
        DateTime,
        nullable=False
    )


    end_time = Column(
        DateTime,
        nullable=False
    )


    duration_minutes = Column(Integer)


    candidate_id = Column(
        String,
        ForeignKey("dim_candidates.candidate_id")
    )


    probability = Column(Float)
    candidate_probability = Column(Float)



class Candidates(Base):
    __tablename__ = "dim_candidates"


    candidate_id = Column(
        String,
        primary_key=True
    )


    semantic_type = Column(String)


    latitude = Column(Float)


    longitude = Column(Float)


class FactActivity(Base):
    __tablename__ = "fact_activity"


    activity_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    start_time = Column(
        DateTime,
        nullable=False
    )


    end_time = Column(
        DateTime,
        nullable=False
    )


    distance_meters = Column(Integer)


    activity_type = Column(String)

    activity_probability = Column(Float)

    start_latitude = Column(Float)

    start_longitude = Column(Float)


    end_latitude = Column(Float)

    end_longitude = Column(Float)




class TimelinePath(Base):
    __tablename__ = "timeline_path"


    path_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    ###############################TENHO QUE ESTUDAR SE CADA PATH É UM PATH DE UMA ACTIVITY OU SE É UM PATH DE UM VISIT, OU SE É UM PATH DE UM LISTENING, OU SE É UM PATH DE UM CONTEXT EVENT. POR ENQUANTO ESTOU COLOCANDO COMO SE FOSSE UM PATH DE UMA ACTIVITY, MAS TENHO QUE ESTUDAR MELHOR ISSO.###############################
    # activity_id = Column(
    #     Integer,
    #     ForeignKey("fact_activity.activity_id"),
    #     nullable=False
    # )

    start_time = Column(
        DateTime,
        nullable=False
    )


    end_time = Column(
        DateTime,
        nullable=False
    )


    latitude = Column(Float)


    longitude = Column(Float)


    duration_minutes_offset = Column(Integer)



# ==========================
# Analytics
# ==========================


class FactContextEvent(Base):
    __tablename__ = "fact_context_event"


    event_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    timestamp = Column(
        DateTime,
        nullable=False
    )


    listening_id = Column(
        Integer,
        ForeignKey("fact_listening.listening_id")
    )


    visit_id = Column(
        Integer,
        ForeignKey("fact_visit.visit_id")
    )


    activity_id = Column(
        Integer,
        ForeignKey("fact_activity.activity_id")
    )


    latitude = Column(Float)

    longitude = Column(Float)