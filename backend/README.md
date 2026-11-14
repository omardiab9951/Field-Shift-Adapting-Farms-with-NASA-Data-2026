# Field Shift API

This backend intentionally consumes one integrated dataset:

```text
data/processed/master_monthly.csv
```

The API validates that file during startup before serving requests. The current
`eda` branch does not yet include the integrated CSV, so startup will fail with
an actionable validation error until the data-integration step produces it.

## Local development

```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend
../.venv/bin/uvicorn app.main:app --reload
```

Run the focused loader tests from the repository root:

```bash
pytest -q backend/tests
```
