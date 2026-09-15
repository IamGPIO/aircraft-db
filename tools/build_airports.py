#!/usr/bin/env python3
"""Airports for the 'where did it land' lookup, from OurAirports (public domain):
https://davidmegginson.github.io/ourairports-data/airports.csv
Output: airports/<lat10>_<lon10>.json - 10x10 degree cells, each a list of
[ident, iata, name, municipality, country, lat, lon, kind] with kind L/M/S (large/medium/small).
Run: python tools/build_airports.py airports.csv"""
import csv, json, math, os, sys
from collections import defaultdict
src = sys.argv[1]
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'airports')
os.makedirs(out, exist_ok=True)
KIND = {'large_airport': 'L', 'medium_airport': 'M', 'small_airport': 'S'}
cells = defaultdict(list); n = 0
with open(src, encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        k = KIND.get(row.get('type', ''))
        if not k: continue
        try: lat, lon = float(row['latitude_deg']), float(row['longitude_deg'])
        except Exception: continue
        cell = f"{math.floor(lat / 10) * 10}_{math.floor(lon / 10) * 10}"
        cells[cell].append([row.get('ident', ''), row.get('iata_code', ''), row.get('name', ''), row.get('municipality', ''),
                            row.get('iso_country', ''), round(lat, 4), round(lon, 4), k]); n += 1
for cell, rows in cells.items():
    with open(os.path.join(out, cell + '.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, separators=(',', ':'), ensure_ascii=False)
print(f'{n} airports in {len(cells)} cells')
