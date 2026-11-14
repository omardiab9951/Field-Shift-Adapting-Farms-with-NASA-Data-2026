# Field Shift API

A local FastAPI backend for the standalone Field Shift V2 site. The API reads
the four pinned CSVs in `data/processed/` once at startup. It does not download
data, access arbitrary filesystem paths, serve the website directory, or make
changes to the frontend.

## Data source and scoring

The inputs and manifest are from the `Final-System` branch at commit
`930ced44d013ac5760b38fee035fea9f5738b657`. The manifest records the source
URLs, SHA-256 hashes, and verified dimensions. Startup verifies each file's
hash and shape before loading.

Scoring uses the published `s_land`, `s_water`, and `s_practice` components:

```text
(land_weight*s_land + water_weight*s_water + practice_weight*s_practice)
/ (land_weight + water_weight + practice_weight)
```

Water scores are not renormalized per cell. Ties use the explicit option order
in the manifest, matching notebook 11's first-in-source-order ranking:
wheat pairs, sugarbeet pairs, potato pairs (summer order maize, rice, cotton,
soybean), then alfalfa. The land-and-water alternative uses weights `1, 1, 0`.
One millimeter over one hectare is reported as `10 m3/ha`.

The API carries these scientific limits: rice net irrigation excludes added
seepage losses; sugarbeet has the notebook's special suitability treatment;
some source values were median-filled and flagged; local practice is based on
area-level 2020 statistics, not a farmer's current rotation; scores are
comparative, not probabilities or guaranteed yields; and detailed calendar
feasibility, profitability, and agronomic rotation rules are not checked.
Source resolution is also limited by the coarser input layers.

Published confidence and robustness describe the notebook's default analysis,
not custom-weight confidence or probability of farming success. Custom
irrigation differences are signed and are not automatically described as
savings.

## Windows setup and operation

From PowerShell:

```powershell
# Backend
Set-Location C:\Users\o3995\Downloads\FieldShift-WebsiteV2\backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another PowerShell window, serve the standalone frontend from the project
root:

```powershell
Set-Location C:\Users\o3995\Downloads\FieldShift-WebsiteV2
py -3.13 -m http.server 8080 --bind 127.0.0.1
```

The checked-in local `.venv` is ignored. Python 3.13 or a compatible newer
Python with pandas wheels can be used. The application resolves data and
manifest paths from its source files, independent of the current directory.
The host and port are fixed at `127.0.0.1:8000`; the allowed browser origins
are explicitly limited to `http://127.0.0.1:8080` and
`http://localhost:8080`. `backend/.env.example` documents these fixed local
settings; they are not environment-overridable.

If inputs are missing or fail validation/integrity checks, `/api/health`
remains available and reports `data_ready: false`. Dataset-dependent routes
return HTTP 503 with a reason; the API does not silently substitute data.

## API

Interactive OpenAPI documentation: <http://127.0.0.1:8000/docs>

Examples (PowerShell):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/data-info
Invoke-RestMethod http://127.0.0.1:8000/api/cells
Invoke-RestMethod http://127.0.0.1:8000/api/cells/1
Invoke-RestMethod http://127.0.0.1:8000/api/cells/1/recommendations
Invoke-RestMethod http://127.0.0.1:8000/api/cells/1/scores

$body = @{
    cell_id = 1
    weights = @{ land = 1; water = 1; practice = 1 }
} | ConvertTo-Json
Invoke-RestMethod -Method Post `
    -Uri http://127.0.0.1:8000/api/rotations/evaluate `
    -ContentType 'application/json' `
    -Body $body
```

Custom weights must be finite and nonnegative with a strictly positive sum.
Unknown cell IDs return 404. Non-farm cells receive no custom recommendations
even though their published scores remain available through the scores route.
Missing input values are kept and serialized as JSON `null`.

## Frontend integration

The standalone frontend's selected-cell recommendation card calls
`GET /api/cells/{cell_id}/recommendations` and
`POST /api/rotations/evaluate`. The small client is `js/api.js`, loaded before
`app.js`. Its default backend URL is `http://127.0.0.1:8000`; to override it,
set `window.FS_API_BASE_URL` in a script loaded before `js/api.js`.

The embedded map ranking and historical charts still use `js/data.js`. Their
migration is not part of this milestone. The card reports when its backend
ranking differs from the embedded map ranking.
