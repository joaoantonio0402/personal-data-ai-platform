from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_GOOGLE_DIR = PROJECT_ROOT / "data" / "raw" / "google"
PROCESSED_GOOGLE_DIR = PROJECT_ROOT / "data" / "processed" / "google"


def find_google_timeline_file(raw_dir: Path | None = None) -> Path | None:
    """Return the most recent Google Timeline JSON file when there is one."""
    directory = raw_dir or RAW_GOOGLE_DIR
    files = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def extract_google_timeline(raw_path: str | Path | None = None) -> pd.DataFrame:
    """Load and normalize all raw Google Timeline JSON files in the folder.

    The Google export can be incremental: each file contains the last extraction plus
    historical rows. Because of that, the incremental check must happen at the data level
    (timestamps already in the database), not by file hash alone.
    """
    if raw_path is not None:
        file_paths = [Path(raw_path)]
    else:
        directory = RAW_GOOGLE_DIR
        file_paths = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime)

    frames = []
    for file_path in file_paths:
        df = pd.read_json(file_path).drop("timelineMemory", axis=1, errors="ignore")
        if df.empty:
            continue
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
        df["endTime"] = pd.to_datetime(df["endTime"], utc=True)
        df["startTime"] = df["startTime"].dt.tz_convert("America/Sao_Paulo")
        df["endTime"] = df["endTime"].dt.tz_convert("America/Sao_Paulo")
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["startTime", "endTime"], keep="last")

    PROCESSED_GOOGLE_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(PROCESSED_GOOGLE_DIR / "google_timeline_raw.csv", index=False)
    return combined
