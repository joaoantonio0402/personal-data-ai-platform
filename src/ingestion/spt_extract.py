from datetime import datetime, timezone

import requests
from pathlib import Path
import json

def extract_lastfm_data_from_date(start_date=None, end_date=None):

    if end_date is None:
        end_date = datetime.now(timezone.utc)

    if start_date is None:
        start_date = datetime(1970, 1, 1, tzinfo=timezone.utc)

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    print(start_timestamp, end_timestamp)
    URL = "https://ws.audioscrobbler.com/2.0/?"
    page=1
    params = {
        "method": "user.getrecenttracks",
        "user": "joaoantonio0402",
        "limit": 200,
        "page": 1,
        "from": start_timestamp,
        "to": end_timestamp,
        "extended": 0,
        "api_key": "71d883bfc3d9583a390b78c46f19f2e4",
        "format": "json"
    }
    response = requests.get(URL, params=params)
    data = response.json()

    total_pages = int(data["recenttracks"]["@attr"]["totalPages"])

    print("Total pages:", total_pages)

    # Diretório para os dados raw
    #Path("raw").mkdir(exist_ok=True)

    PROJECT_ROOT = Path(__file__).resolve().parents[2]

    today = datetime.now().strftime("%Y-%m-%d")

    raw_dir = PROJECT_ROOT / "data" / "raw" / "spotify" / today
    pages_dir = raw_dir / "pages"

    pages_dir.mkdir(parents=True, exist_ok=True)

    # Salvar cada página exatamente como veio da API
    for page in range(1, total_pages + 1):

        print(f"Buscando página {page}/{total_pages}")

        params["page"] = page

        response = requests.get(URL, params=params)
        response.raise_for_status()

        data = response.json()

        with open(f"data/raw/spotify/{today}/pages/lastfm_page_{page}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    raw_dir = Path(f"data/raw/spotify/{today}/pages/")
    json_files = sorted(raw_dir.glob("*.json"))
    
    print(f"Arquivos encontrados: {len(json_files)}")

    all_tracks = []

    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        tracks = data["recenttracks"]["track"]

        all_tracks.extend(tracks)

    print(f"Total de registros: {len(all_tracks)}")

    with open(f"data/raw/spotify/{today}/lastfm_recenttracks.json", "w", encoding="utf-8") as f:
        json.dump(all_tracks, f, ensure_ascii=False, indent=2)

extract_lastfm_data_from_date()
