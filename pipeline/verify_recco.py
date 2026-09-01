import json
import requests

# Real API probe
print('--- real search ---')
for q in ['Hair Down', 'Without Me', 'Shape of You']:
    r = requests.get('https://api.reccobeats.com/v1/track/search', params={'searchText': q}, timeout=20)
    data = r.json() or {}
    print(q, r.status_code, 'count=', len((data.get('content') or [])))
    if data.get('content'):
        first = data['content'][0]
        print('first id=', first.get('id'))
        print('first title=', first.get('trackTitle'))
        print('first artists=', first.get('artists', [])[:2])
        track_id = first.get('id')
        if track_id:
            f = requests.get(f'https://api.reccobeats.com/v1/track/{track_id}/audio-features', timeout=20)
            print('features status=', f.status_code)
            print(f.text[:300])
    print('---')

# Local contract probe
print('--- local contract ---')
from src.clients import reccobeats_client
from unittest.mock import patch

class Resp:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
    def raise_for_status(self):
        return None
    def json(self):
        return self.payload

payload = {'data': {'id': 'abc123', 'acousticness': 0.5, 'danceability': 0.7, 'energy': 0.9, 'instrumentalness': 0.1, 'key': 1, 'liveness': 0.2, 'loudness': -6.2, 'mode': 1, 'speechiness': 0.3, 'tempo': 110.0, 'valence': 0.4, 'href': '/x', 'isrc': 'US123'}}
with patch.object(reccobeats_client.requests, 'get', return_value=Resp(payload)):
    result = reccobeats_client.get_audio_features('https://api.reccobeats.com/v1/track/abc123')
    print(result)
