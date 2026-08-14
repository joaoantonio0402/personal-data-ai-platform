from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import declarative_base


Base = declarative_base()


# ==========================
# Spotify
# ==========================

class DimArtist(Base):
    __tablename__ = "dim_artist"

    artist_id = Column(
            Integer,
            primary_key=True,
            autoincrement=True
        )
    
    artist_mbid = Column(String)
    artist_name = Column(String)
    followers = Column(Integer)
    popularity = Column(Integer)



class DimAlbum(Base):
    __tablename__ = "dim_album"

    album_id = Column(
                Integer,
                primary_key=True,
                autoincrement=True
            )
    album_mbid = Column(String)
    album_name = Column(String)
    release_date = Column(Date)
    artist_id = Column(
            Integer,
            ForeignKey("dim_artist.artist_id"),
            nullable=False
        )



class DimTrack(Base):
    __tablename__ = "dim_track"

    track_id = Column(
                Integer,
                primary_key=True,
                autoincrement=True
            )
    track_mbid = Column(String)
    track_name = Column(String)

    artist_id = Column(
        Integer,
        ForeignKey("dim_artist.artist_id"),
        nullable=False
    )

    album_id = Column(
        Integer,
        ForeignKey("dim_album.album_id"),
        nullable=False
    )

    duration_ms = Column(Integer)

    danceability = Column(Float)
    energy = Column(Float)
    valence = Column(Float)
    tempo = Column(Float)

    genre = Column(String)



class FactListening(Base):
    __tablename__ = "fact_listening"

    listening_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    timestamp_utc = Column(
        DateTime,
        nullable=False
    )

    timestamp_uts = Column(
        Integer,
        nullable=False
    )

    track_id = Column(
        Integer,
        ForeignKey("dim_track.track_id"),
        nullable=False
    )

    duration_ms = Column(Integer)

    platform = Column(String)



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