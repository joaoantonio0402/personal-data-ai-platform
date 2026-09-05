import pandas as pd


def stage_google_data(data: dict) -> dict:
    """Basic validation and staging for Google timeline dataframes."""
    cleaned = {}

    for key, frame in data.items():
        if frame is None or not isinstance(frame, pd.DataFrame):
            continue
        cleaned[key] = frame.drop_duplicates().reset_index(drop=True)

    return cleaned
