#!/usr/bin/env python3
"""
Build the Flight Light aircraft lookup shards.

Sources (both free):
  * FAA Releasable Aircraft database  https://registry.faa.gov/database/ReleasableAircraft.zip
    (public domain; authoritative for every US N-number)
  * OpenSky Network aircraft database https://opensky-network.org/datasets/metadata/aircraftDatabase.csv
    (crowd-sourced worldwide list; used only for hexes the FAA file does not cover)

Output: shards/<first 3 hex chars>.json, each mapping hex -> [reg, manufacturer, model, typecode, operator, year, src]
plus index.json with counts and the build date. flightlight.uk fetches one shard per lookup and caches per hex.

Run:  python tools/build.py <ReleasableAircraft.zip> <aircraftDatabase.csv>
"""
import csv, io, json, os, sys, time, zipfile
from collections import defaultdict

csv.field_size_limit(10_000_000)
zip_path, opensky_path = sys.argv[1], sys.argv[2]
out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shards')
os.makedirs(out_dir, exist_ok=True)

records = {}   # hex -> [reg, mfr, model, typecode, operator, year, src]

# ---- FAA ----
z = zipfile.ZipFile(zip_path)
ref = {}
with z.open('ACFTREF.txt') as f:
    rd = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', errors='replace'))
    hdr = [h.strip() for h in next(rd)]
    ci = {h: i for i, h in enumerate(hdr)}
    for row in rd:
        if len(row) < 3: continue
        ref[row[ci['CODE']].strip()] = (row[ci['MFR']].strip().title(), row[ci['MODEL']].strip())
faa = 0
with z.open('MASTER.txt') as f:
    rd = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', errors='replace'))
    hdr = [h.strip() for h in next(rd)]
    ci = {h: i for i, h in enumerate(hdr)}
    i_n, i_code, i_year, i_hex = ci['N-NUMBER'], ci['MFR MDL CODE'], ci['YEAR MFR'], ci['MODE S CODE HEX']
    for row in rd:
        if len(row) <= i_hex: continue
        hx = row[i_hex].strip().lower()
        if len(hx) != 6: continue
        mfr, model = ref.get(row[i_code].strip(), ('', ''))
        year = row[i_year].strip()
        records[hx] = ['N' + row[i_n].strip(), mfr, model, '', '', year if year.isdigit() else '', 'FAA']
        faa += 1

# ---- FAA deregistered (an aircraft can keep flying on its old hex after its N-number is cancelled) ----
dereg = 0
latest = {}
with z.open('DEREG.txt') as f:
    rd = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', errors='replace'))
    hdr = [h.strip() for h in next(rd)]
    ci = {h: i for i, h in enumerate(hdr)}
    i_n, i_code, i_year, i_hex, i_cancel = ci['N-NUMBER'], ci['MFR-MDL-CODE'], ci['YEAR-MFR'], ci['MODE S CODE HEX'], ci['CANCEL-DATE']
    for row in rd:
        if len(row) <= i_hex: continue
        hx = row[i_hex].strip().lower()
        if len(hx) != 6 or hx in records: continue
        cancel = row[i_cancel].strip()
        if hx in latest and latest[hx][0] >= cancel: continue
        mfr, model = ref.get(row[i_code].strip(), ('', ''))
        year = row[i_year].strip()
        note = 'deregistered ' + (cancel[:4] + '-' + cancel[4:6] if len(cancel) == 8 else cancel)
        latest[hx] = (cancel, ['N' + row[i_n].strip(), mfr, model, '', '', year if year.isdigit() else '', 'FAA-dereg', note])
for hx, (_, rec) in latest.items():
    records[hx] = rec; dereg += 1

# ---- OpenSky (fills what the FAA file does not cover) ----
osk = 0
with open(opensky_path, encoding='utf-8', errors='replace', newline='') as f:
    rd = csv.DictReader(f)
    for row in rd:
        hx = (row.get('icao24') or '').strip().lower()
        if len(hx) != 6 or hx in records: continue
        reg = (row.get('registration') or '').strip()
        model = (row.get('model') or '').strip()
        if not reg and not model: continue
        built = (row.get('built') or '').strip()[:4]
        records[hx] = [reg, (row.get('manufacturername') or '').strip(), model, (row.get('typecode') or '').strip(),
                       (row.get('operator') or '').strip(), built if built.isdigit() else '', 'OpenSky']
        osk += 1

# ---- shards ----
shards = defaultdict(dict)
for hx, rec in records.items():
    shards[hx[:3]][hx] = rec
for k, v in shards.items():
    with open(os.path.join(out_dir, k + '.json'), 'w', encoding='utf-8') as f:
        json.dump(v, f, separators=(',', ':'), ensure_ascii=False)
with open(os.path.join(os.path.dirname(out_dir), 'index.json'), 'w', encoding='utf-8') as f:
    json.dump({'built': time.strftime('%Y-%m-%d'), 'faa': faa, 'faa_dereg': dereg, 'opensky': osk, 'total': len(records), 'shards': len(shards),
               'fields': ['reg', 'manufacturer', 'model', 'typecode', 'operator', 'year', 'src', 'note']}, f, indent=2)
print(f'FAA {faa} + FAA-dereg {dereg} + OpenSky {osk} = {len(records)} aircraft in {len(shards)} shards')
for probe in ('a7ecad', '407fc9'):
    print(probe, '->', records.get(probe))
