#!/usr/bin/env python3
"""Chart cells for the Flight Light map's aviation layer, from OurAirports (public domain):
https://davidmegginson.github.io/ourairports-data/airports.csv
https://davidmegginson.github.io/ourairports-data/runways.csv
Output: chart/<lat5>_<lon5>.json - 5x5 degree cells:
  {"airports": [[ident, iata, name, lat, lon, kind]],            kind L/M/S/H (large/medium/small/heliport)
   "runways":  [[airport_ident, le_lat, le_lon, he_lat, he_lon, length_ft, surface, le_ident, he_ident, lighted, closed]]}
Only runways with both end positions are drawn (about a third of the world's, all the ones that matter).
Run: python tools/build_chart.py airports.csv runways.csv"""
import csv, json, math, os, sys
from collections import defaultdict
airports_csv, runways_csv = sys.argv[1], sys.argv[2]
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chart')
os.makedirs(out, exist_ok=True)
KIND = {'large_airport': 'L', 'medium_airport': 'M', 'small_airport': 'S', 'heliport': 'H'}
cells = defaultdict(lambda: {'airports': [], 'runways': []})
def cell(lat, lon): return f"{math.floor(lat / 5) * 5}_{math.floor(lon / 5) * 5}"
na = nr = 0
with open(airports_csv, encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        k = KIND.get(row.get('type', ''))
        if not k: continue
        try: lat, lon = float(row['latitude_deg']), float(row['longitude_deg'])
        except Exception: continue
        cells[cell(lat, lon)]['airports'].append([row.get('ident', ''), row.get('iata_code', ''), row.get('name', ''), round(lat, 4), round(lon, 4), k]); na += 1
with open(runways_csv, encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        try:
            a, b, c, d = (float(row['le_latitude_deg']), float(row['le_longitude_deg']), float(row['he_latitude_deg']), float(row['he_longitude_deg']))
        except Exception: continue
        if abs(a) > 90 or abs(c) > 90 or abs(b) > 180 or abs(d) > 180: continue
        try: length = int(float(row.get('length_ft') or 0))
        except Exception: length = 0
        cells[cell((a + c) / 2, (b + d) / 2)]['runways'].append([row.get('airport_ident', ''), round(a, 5), round(b, 5), round(c, 5), round(d, 5), length,
                                                                  (row.get('surface') or '')[:12], row.get('le_ident', ''), row.get('he_ident', ''),
                                                                  1 if row.get('lighted') == '1' else 0, 1 if row.get('closed') == '1' else 0]); nr += 1
for name, data in cells.items():
    with open(os.path.join(out, name + '.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
print(f'{na} airports and {nr} runways in {len(cells)} cells')
