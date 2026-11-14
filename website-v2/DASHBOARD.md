# Field Shift — connected local dashboard

## Run

**Windows:** double-click `run-local.bat`. The first run creates `backend/.venv` and installs the requirements; every run starts the server and opens http://127.0.0.1:8000. Keep the window open.

**macOS / Linux:**

The backend now serves the dashboard and its CSS/JS on the same origin:

```sh
./run-local.sh
```

Open http://127.0.0.1:8000. No separate static server is required. An existing preview on port 8080 can also use the backend at port 8000, through its explicitly allowed CORS origin.

First-time setup, from `website-v2/backend`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pytest -q
```

Browser storage is scoped to the URL origin: existing local farms on port 8080 remain there; they are not automatically migrated to port 8000.

## Data contract

- `GET /api/dashboard/catalog`: eligible cells and the original Sidi Salem & Qallin pilot footprint.
- `POST /api/dashboard/evaluate`: cell profile, historical monthly rain/temperature, all 13 ranked rotations, normalized weights and source revision, from the existing ScoringService. Optional `area_feddan` returns annual modeled irrigation volume (mm × feddan × 4.2).
- `GET /api/dashboard/science`: study identity, actual dataset dimensions and sources read from the 189-field CSV dictionary.
- `POST /api/dashboard/match`: validated geographic coordinates matched to the closest study cell; rejects nonfarm cells and locations outside coverage or more than 750 m away.
- Existing `/api/cells`, `/api/rotations/evaluate`, `/api/health`, and `/api/data-info` remain available.

The dashboard no longer loads `dashboard-data.js` or computes rankings locally. It makes abortable, time-limited requests. Failed requests hide stale metrics and provide retry; stale responses cannot replace a newer selection. Draft weight previews are debounced and scored by the backend too.

The original CSVs, hashes, notebook option order, missing-value flags, scoring formula, and published confidence semantics remain unchanged. Scores compare rotations, not probabilities or guaranteed yields. Annual irrigation is modeled net irrigation, not measured consumption; rice seepage is excluded. More detail is available inside the methodology disclosure on Crop Insights.

## Study area and cell selection

The original project presentation identifies the pilot as near **Sidi Salem and Qallin, Kafr El Sheikh** (`story.html`, original project footer). The CSV footprint is approximately latitude 31.051–31.298 and longitude 30.704–30.909. There are no administrative district memberships in the CSV; the previous invented four-sector selector was removed. The backend catalog now exposes one named pilot footprint and each eligible cell's original row, column and coordinates.

Users choose a real cell by number or from the study grid. Nonfarm cells are not selectable. Existing saved farms retain their cell IDs; obsolete study-sector selections safely fall back to the real study footprint. Selected cell IDs persist across refresh. This does not imply that every cell is inside Sidi Salem's administrative boundary.

The Science view is an internal dashboard page; its button no longer navigates to the old presentation. Counts and source lists come from `/api/dashboard/science`, not a second handwritten dataset. The original source commit remains linked in a disclosure.

Crop Insights compares the top three rotations and their component scores. Saved farm area converts modeled irrigation depth to volume on the backend using 1 feddan = 4,200 m². Changing area does not change dimensionless crop scores. The historical month selector uses the exact `rain_mm_mXX` and `t_max_c_mXX` fields; it is not a forecast.

A new farm is matched server-side. Its map and profile use the matched cell center. Browsing study cells does not create a fictional owned farm; users explicitly add a farm to save a checklist.

## Maps

The map is one Leaflet 1.9.4 map (`js/vendor/leaflet.js`, bundled, no CDN, no API key), built once and moved into the overview card on every render. Changing the page, language, theme, month or weights does not rebuild or reload it.

- **Imagery:** Esri World Imagery tiles. If they cannot load, the map switches to Sentinel-2 cloudless (EOX). If both fail, a notice says so and the grid stays visible.
- **Study grid:** all 560 cells from `GET /api/dashboard/catalog` (`grid`), with corner coordinates. The CSV stores centres only; a second-order fit of lat/lon on (col, row) reproduces every centre to within 0.1 m and gives the corners at col ± 0.5, row ± 0.5. Village/water cells are grey and dashed.
- **Selection:** the selected cell is outlined in gold. Clicking a farm cell selects it and re-scores it on the backend. The outline is a 1 km data cell, not a surveyed farm boundary.
- Wheel zoom turns on only after a click into the map, so the page scrolls normally.

Why not the Google embed: the previous version built a keyless `google.com/maps/embed?pb=` URL by hand and rebuilt the iframe on every render. That URL is not a supported API and Google can blank or rate-limit it, and the iframe had no CSS size, so it sometimes showed as a 300×150 strip.

## Windows checkouts

`core.autocrlf` rewrites the data CSVs with CRLF line endings, which changed their SHA-256 and made the backend refuse its data. `website-v2/.gitattributes` now keeps `backend/data/**` byte-for-byte, and the hash check also accepts a file whose only difference is CRLF line endings. Any other change still fails.

## Saved options

Farms, selected location, language, theme, weights and per-farm tasks are local to this browser. Reports export JSON containing the selected cell, weights, server results and source revision. No user account, server-side farm persistence or device sync is implemented.

The original presentation remains at `/story.html`. Only public CSS/JS and the two HTML pages are served; backend files and the virtual environment are not publicly mounted.
