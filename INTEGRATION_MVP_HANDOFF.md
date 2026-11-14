# Field Shift Integration MVP Handoff

This document explains the work completed on the `integration-mvp` branch and
how the team should continue building the NASA Space Apps MVP.

The guiding decision for this branch is:

> The backend consumes one integrated CSV only. Source datasets are harmonized
> and merged before the backend starts.

## 1. Branch and current status

The branch was created from the latest fetched `origin/eda` commit:

```text
integration-mvp
```

The branch currently contains the initial FastAPI foundation and the single-CSV
loader. It does not yet contain `master_monthly.csv`, because that file still
needs to be produced by the data-integration work.

The API is deliberately configured to fail during startup when the integrated
dataset is missing or invalid. This prevents the team from presenting results
from incomplete or incorrectly merged data.

## 2. What was added

### Backend files

```text
backend/
  README.md
  requirements.txt
  pytest.ini
  app/
    __init__.py
    config.py
    data_loader.py
    main.py
  tests/
    test_data_loader.py
```

### `backend/app/config.py`

Defines the shared data contract:

- Default dataset path:
  `data/processed/master_monthly.csv`
- Expected cells: `560`
- Expected monthly periods: `108`
- Expected period: `2016-01` through `2024-12`
- Required key columns:
  `cell_id`, `lat`, `lon`, `year`, and `month`

Keep these values centralized. Future API modules should import them instead of
duplicating constants.

### `backend/app/data_loader.py`

Provides:

- `load_master_dataset(...)`
- `MasterDataset`
- `DatasetValidationError`

The loader reads only the integrated CSV. It does not load or merge any source
CSV files.

### `backend/app/main.py`

Creates the FastAPI application and loads the dataset through the application
lifespan. The dataset must pass validation before the API serves requests.

The currently implemented endpoint is:

```text
GET /api/health
```

It reports the loaded dataset path, row count, column count, cell count, and
number of year/month periods.

### `backend/tests/test_data_loader.py`

Tests the loader against valid and invalid CSVs, including:

- Missing files.
- Missing required columns.
- Invalid months.
- Duplicate cell/month keys.
- Invalid fill values such as `-999`.
- Successful loading of a valid dataset.

## 3. Integrated CSV contract

The required backend input is:

```text
data/processed/master_monthly.csv
```

The file must have one row for every grid cell and month:

```text
560 cells × 108 months = 60,480 rows
```

The date range is:

```text
2016-01 through 2024-12
```

### Required identity columns

```text
cell_id
lat
lon
year
month
```

The combination below must be unique:

```text
(cell_id, year, month)
```

### Recommended integrated data columns

The exact scientific column names should be agreed by the data team before the
merge is finalized. The integrated file should contain the following categories.

#### Climate

- Monthly rainfall totals.
- Mean, maximum, and minimum temperature.
- Relative humidity.
- Wind.
- Solar radiation.

#### Soil moisture and water

- Surface soil moisture.
- Root-zone soil moisture.
- Soil-moisture anomaly.
- Evapotranspiration or crop-water proxy.
- Water-balance indicator.

#### Satellite vegetation

- NDVI.
- Bare-field percentage.
- Low-cover percentage.
- Valid-observation percentage.

#### Static cell characteristics

- Elevation.
- Slope or an erosion proxy.
- Soil properties or soil suitability.
- Any documented local suitability fields.

#### Derived signals

- Heat-stress days.
- Frost days.
- Rainfall trend.
- Rainfall variability.
- Extreme-rain indicator.
- Erosion-risk indicator.
- Crop-stress indicator.

#### Data-quality fields

Include explicit flags wherever possible:

- Missing-value flags.
- Imputation flags.
- Cloud or invalid-observation flags.
- Coarse-resolution flags.
- Source-agreement or disagreement flags.

These fields will later support the confidence score and information-gap
messages shown to judges and users.

## 4. Data-team next steps

The data team should complete the merge before the backend scoring work begins.

### Step 1: Finish the source-data checks

Confirm that the processed files are present and valid:

```text
grid_1km.csv
power_monthly.csv
gpm_monthly.csv
smap_monthly.csv
sentinel2_monthly.csv
srtm_static.csv
gaez_static.csv, if used
landsat_yearly.csv
```

The existing data workflow says that `landsat_yearly.csv` remains yearly. For
the single-CSV backend design, convert its useful trend information into
cell-level fields and join those fields to every monthly row for that cell.

### Step 2: Build the integrated table

Create the complete cell-by-month table using:

```text
grid cells × 2016-01 through 2024-12
```

Join:

- Per-cell monthly data on `cell_id`, `year`, and `month`.
- Area-wide monthly data on `year` and `month`.
- Static data on `cell_id`.
- Yearly trend data on `cell_id` and `year`, then repeat it for that year’s
  monthly rows.

### Step 3: Validate before committing

The merge process should confirm:

```text
Rows: 60,480
Unique cells: 560
Unique year/month periods: 108
Duplicate (cell_id, year, month) keys: 0
```

Also confirm:

- No fill values such as `-999` remain.
- Missing values are represented as empty CSV fields.
- Numeric columns are numeric.
- Every cell has exactly 108 rows.
- Static attributes do not vary unexpectedly within a cell.

### Step 4: Save the final file

Save exactly:

```text
data/processed/master_monthly.csv
```

Do not rename the file without also updating
`backend/app/config.py`. Do not make the backend depend on individual source
files.

## 5. Local backend setup

Use a virtual environment. Do not install project dependencies into the system
Python installation.

From the repository root:

```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

Run the tests:

```bash
.venv/bin/pytest -q backend/tests
```

Start the API from the repository root:

```bash
.venv/bin/uvicorn app.main:app --app-dir backend --reload
```

When `master_monthly.csv` is present and valid, check:

```text
http://127.0.0.1:8000/api/health
```

Interactive API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

If the integrated CSV is missing, startup should fail with a message identifying
the required path. This is expected until the data merge is complete.

## 6. How future backend work should be added

The next backend developer should preserve this separation:

```text
CSV loader → dataset service → signals/aggregations → scoring engine → API routes
```

Do not put data-merging logic inside FastAPI routes. Do not read source CSVs
from route handlers. The API should receive a validated `MasterDataset` and
operate on that single in-memory table.

Recommended future files:

```text
backend/app/
  schemas.py
  dataset_service.py
  scoring_engine.py
  confidence_service.py
  explanation_service.py
  routes/
    cells.py
    scoring.py
    metadata.py
```

### Dataset service

Add read-only query methods for:

- Listing cells.
- Returning one cell’s monthly records.
- Returning one cell’s 108-month summary.
- Selecting only requested columns for chart responses.

### Scoring engine

Implement three options:

1. Baseline/current rotation.
2. Nitrogen-fixing rotation.
3. Water-saving rotation.

Score each option from 0 to 1 for:

- Water use.
- Soil health.
- Erosion reduction.
- Pest-cycle breaking.
- Income potential.
- Climate fit.

The final score must be a weighted average based on user priorities. Every
response should include the individual criterion scores and the evidence values
used to calculate them.

### Confidence service

Use the integrated data-quality fields and farmer inputs to identify:

- Missing or imputed observations.
- Coarse-resolution limitations.
- Missing soil information.
- Generalized crop facts.
- Unknown market or equipment constraints.
- Conflicting signals.

Return confidence as `high`, `medium`, or `low`, together with explicit
information gaps and local-review warnings.

## 7. Recommended API sequence

The following endpoints can be added incrementally:

```text
GET  /api/health
GET  /api/metadata
GET  /api/cells
GET  /api/cells/{cell_id}/summary
GET  /api/cells/{cell_id}/monthly
POST /api/score-rotations
```

`/api/health` is already implemented. The remaining endpoints should be added
without changing the loader contract.

## 8. Frontend handoff

The frontend should communicate with the backend only through HTTP endpoints.
It should not import pandas, read the CSV, or calculate scientific values in
the browser.

Recommended screen order:

1. Select a grid cell on the Sidi Salem Leaflet map.
2. Enter the current crop rotation.
3. Enter optional water, equipment, soil, and market constraints.
4. Adjust priority sliders.
5. View the three scored rotation options.

The results screen must show more than a recommendation:

- Overall score.
- Individual criterion scores.
- Evidence signals.
- Confidence.
- Information gaps.
- Local expert review warnings.
- The statement that the tool supports, but does not replace, farmer and
  expert judgment.

## 9. Team collaboration rules

Before starting work:

```bash
git fetch origin
git switch integration-mvp
git pull --ff-only
```

Keep changes focused by area:

- Data team: integrated CSV and merge validation.
- Backend team: loader, query service, scoring, and API routes.
- Frontend team: map, forms, sliders, and dashboard.
- QA team: tests, demo scenarios, and validation evidence.

Before pushing:

```bash
git diff --check
.venv/bin/pytest -q backend/tests
git status --short
```

Do not commit:

- Raw satellite downloads.
- NASA credentials.
- Virtual environments.
- Python cache directories.
- Large temporary files.

## 10. Definition of done for the base backend

The base backend is ready for the next team phase when:

- `master_monthly.csv` exists at the required path.
- Startup validation succeeds.
- `/api/health` reports 60,480 rows, 560 cells, and 108 periods.
- Loader tests pass.
- The backend can be started without downloading data.
- The next developer can add API routes without changing CSV loading.

The current branch has completed the project structure, loader, validation
logic, health endpoint, tests, and this handoff documentation. The immediate
blocker is the data team's production of the validated integrated CSV.
