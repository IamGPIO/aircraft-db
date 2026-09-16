# aircraft-db

Aircraft identity lookup for Flight Light: hex code -> registration, manufacturer, model, type, operator, year.

Built from the FAA Releasable Aircraft database (public domain; active and deregistered files) and, for hexes the FAA does not cover, the OpenSky Network aircraft database (attribution: opensky-network.org; check its terms before commercial use).

`shards/<first three hex characters>.json` maps hex -> `[reg, manufacturer, model, typecode, operator, year, src, note]`. `index.json` records the build date and counts. flightlight.uk fetches one shard per lookup and caches each aircraft for a month.

Refresh (monthly is plenty):

    curl -L -A "Mozilla/5.0" -o ReleasableAircraft.zip https://registry.faa.gov/database/ReleasableAircraft.zip
    curl -L -o aircraftDatabase.csv https://opensky-network.org/datasets/metadata/aircraftDatabase.csv
    python tools/build.py ReleasableAircraft.zip aircraftDatabase.csv
    git add -A && git commit -m "Refresh" && git push

## Chart cells (`chart/<lat5>_<lon5>.json`)

For the map's aviation layer: 5x5 degree cells of `{"airports": [[ident, iata, name, lat, lon, kind]], "runways": [[airport_ident, le_lat, le_lon, he_lat, he_lon, length_ft, surface, le_ident, he_ident, lighted, closed]]}` with kind L/M/S/H. Built by `tools/build_chart.py` from OurAirports `airports.csv` + `runways.csv` (public domain). Only runways with both end positions are included.
