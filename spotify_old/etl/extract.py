import requests
import pandas as pd

def extract_and_save():

    URL = "https://ws.audioscrobbler.com/2.0/?"

    page=1

    params = {
        "method": "user.getrecenttracks",
        "user": "joaoantonio0402",
        "limit": 2,
        "page": page,
        "extended": 0,
        "api_key": "71d883bfc3d9583a390b78c46f19f2e4",
        "format": "json"
    }

    response = requests.get(URL, params=params)

    data = response.json()

    print(data)

    # total_pages = int(data["recenttracks"]["@attr"]["totalPages"])

    # print("Total pages: ", total_pages)

    # rows = []

    # for page in range(1, total_pages + 1):

    #     print(f"Buscando página {page}")

    #     params["page"] = page

    #     response = requests.get(URL, params=params)

    #     data = response.json()

    #     tracks = data["recenttracks"]["track"]

    #     for track in tracks:

    #         row = {

    #             "track": track["name"],

    #             "artist": track["artist"]["#text"],

    #             "album": track["album"]["#text"],

    #             "utc_time": pd.to_datetime(track["date"]["#text"], format="%d %b %Y, %H:%M"),

    #             "uts": track["date"]["uts"]
    #         }
            
    #         rows.append(row)

    # df = pd.DataFrame(rows)

    # df.to_csv("listening_history.csv")
