from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MASTER_DATA_PATH = REPOSITORY_ROOT / "data" / "processed" / "master_monthly.csv"

EXPECTED_CELL_COUNT = 560
EXPECTED_MONTH_COUNT = 108
START_YEAR = 2016
END_YEAR = 2024

REQUIRED_COLUMNS = {
    "cell_id",
    "lat",
    "lon",
    "year",
    "month",
}

KEY_COLUMNS = ["cell_id", "year", "month"]
