from datetime import datetime, timezone
import json
import os
from pathlib import Path
from dotenv import load_dotenv

import requests

load_dotenv()

def extract_lastfm_data_from_date(start_date=None, end_date=None):
    if end_date is None:
        end_date = int(datetime.now(timezone.utc).timestamp())

    if start_date is None:
        start_date = int(datetime(1970, 1, 1, tzinfo=timezone.utc).timestamp())

    start_timestamp = int(start_date)
    end_timestamp = int(end_date)

    print(start_timestamp, end_timestamp)
    URL = "https://ws.audioscrobbler.com/2.0/?"
    params = {
        "method": "user.getrecenttracks",
        "user": "joaoantonio0402",
        "limit": 200,
        "page": 1,
        "from": start_timestamp,
        "to": end_timestamp,
        "extended": 0,
        "api_key": os.getenv("LASTFM_API_KEY"),
        "format": "json",
    }
    response = requests.get(URL, params=params)
    data = response.json()

    total_pages = int(data["recenttracks"]["@attr"]["totalPages"])

    print("Total pages:", total_pages)

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    today_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    raw_dir = PROJECT_ROOT / "data" / "raw" / "spotify" / today_id
    pages_dir = raw_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    for page in range(1, total_pages + 1):
        print(f"Buscando página {page}/{total_pages}")
        params["page"] = page

        response = requests.get(URL, params=params)
        response.raise_for_status()

        data = response.json()

        with open(pages_dir / f"lastfm_page_{page}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    json_files = sorted(pages_dir.glob("*.json"))
    print(f"Arquivos encontrados: {len(json_files)}")

    all_tracks = []

    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        tracks = data["recenttracks"]["track"]
        all_tracks.extend(tracks)

    print(f"Total de registros: {len(all_tracks)}")

    with open(raw_dir / "lastfm_recenttracks.json", "w", encoding="utf-8") as f:
        json.dump(all_tracks, f, ensure_ascii=False, indent=2)

    return str(today_id)


# if __name__ == "__main__":
#     extract_lastfm_data_from_date(start_date=int(datetime.now(timezone.utc).timestamp()) - 86400)
