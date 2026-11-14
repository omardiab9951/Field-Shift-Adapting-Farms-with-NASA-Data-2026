from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import (
    DEFAULT_MASTER_DATA_PATH,
    END_YEAR,
    EXPECTED_CELL_COUNT,
    EXPECTED_MONTH_COUNT,
    KEY_COLUMNS,
    REQUIRED_COLUMNS,
    START_YEAR,
)


class DatasetValidationError(ValueError):
    """Raised when the integrated master dataset violates its contract."""


@dataclass(frozen=True)
class MasterDataset:
    """Validated, read-only view of the integrated monthly dataset."""

    frame: pd.DataFrame
    path: Path


def load_master_dataset(
    path: Path = DEFAULT_MASTER_DATA_PATH,
    *,
    expected_cell_count: int = EXPECTED_CELL_COUNT,
    expected_month_count: int = EXPECTED_MONTH_COUNT,
) -> MasterDataset:
    """Load and validate the single integrated CSV used by the API."""
    path = Path(path)
    if not path.is_file():
        raise DatasetValidationError(
            f"Master dataset not found at {path}. "
            "Create data/processed/master_monthly.csv before starting the API."
        )

    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Unable to read master dataset at {path}: {exc}") from exc

    _validate_schema(
        frame,
        path=path,
        expected_cell_count=expected_cell_count,
        expected_month_count=expected_month_count,
    )
    frame = frame.copy()
    frame["cell_id"] = frame["cell_id"].astype(int)
    frame["year"] = frame["year"].astype(int)
    frame["month"] = frame["month"].astype(int)
    frame.set_flags(allows_duplicate_labels=False)
    return MasterDataset(frame=frame, path=path)


def _validate_schema(
    frame: pd.DataFrame,
    *,
    path: Path,
    expected_cell_count: int,
    expected_month_count: int,
) -> None:
    missing_columns = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing_columns:
        raise DatasetValidationError(
            f"{path}: missing required columns: {', '.join(missing_columns)}"
        )

    if frame.empty:
        raise DatasetValidationError(f"{path}: dataset is empty")

    if frame[KEY_COLUMNS].isna().any().any():
        raise DatasetValidationError(f"{path}: key columns cannot contain missing values")

    for column in ("cell_id", "year", "month"):
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise DatasetValidationError(f"{path}: {column} must be numeric")

    if not frame["year"].between(START_YEAR, END_YEAR).all():
        raise DatasetValidationError(
            f"{path}: year values must be between {START_YEAR} and {END_YEAR}"
        )
    if not frame["month"].between(1, 12).all():
        raise DatasetValidationError(f"{path}: month values must be between 1 and 12")

    duplicate_keys = frame.duplicated(KEY_COLUMNS)
    if duplicate_keys.any():
        count = int(duplicate_keys.sum())
        raise DatasetValidationError(
            f"{path}: found {count} duplicate ({', '.join(KEY_COLUMNS)}) rows"
        )

    cell_count = frame["cell_id"].nunique()
    if cell_count != expected_cell_count:
        raise DatasetValidationError(
            f"{path}: expected {expected_cell_count} cells, found {cell_count}"
        )

    month_count = frame[["year", "month"]].drop_duplicates().shape[0]
    if month_count != expected_month_count:
        raise DatasetValidationError(
            f"{path}: expected {expected_month_count} year/month periods, found {month_count}"
        )

    expected_row_count = expected_cell_count * expected_month_count
    if len(frame) != expected_row_count:
        raise DatasetValidationError(
            f"{path}: expected {expected_row_count} rows, found {len(frame)}"
        )

    rows_per_cell = frame.groupby("cell_id").size()
    if not (rows_per_cell == expected_month_count).all():
        raise DatasetValidationError(
            f"{path}: every cell must have exactly {expected_month_count} monthly rows"
        )

    numeric = frame.select_dtypes(include="number")
    if (numeric <= -999).any().any():
        raise DatasetValidationError(
            f"{path}: numeric columns contain -999 or lower fill values"
        )
