import requests, json
queries = ["Hair Down", "Without Me", "Shape of You"]
for q in queries:
    r = requests.get('https://api.reccobeats.com/v1/track/search', params={'searchText': q}, timeout=20)
    print('QUERY:', q, 'STATUS:', r.status_code)
    data = r.json() or {}
    print('keys:', sorted(data.keys()))
    content = data.get('content') or []
    print('count:', len(content))
    if content:
        first = content[0]
        print(json.dumps({
            'id': first.get('id'),
            'trackTitle': first.get('trackTitle'),
            'name': first.get('name'),
            'artists': first.get('artists', [])[:2],
            'href': first.get('href'),
        }, ensure_ascii=False)[:800])
    print('---')
    print()
