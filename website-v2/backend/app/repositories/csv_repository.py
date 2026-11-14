import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.core.errors import DataLoadError

REQUIRED_FILES = (
    "master_cell.csv",
    "master_cell_dictionary.csv",
    "scores_all.csv",
    "recommendations.csv",
)

OPTION_ORDER = (
    "wheat -> maize",
    "wheat -> rice",
    "wheat -> cotton",
    "wheat -> soybean",
    "sugarbeet -> maize",
    "sugarbeet -> rice",
    "sugarbeet -> cotton",
    "sugarbeet -> soybean",
    "potato -> maize",
    "potato -> rice",
    "potato -> cotton",
    "potato -> soybean",
    "alfalfa (all year)",
)
OPTION_ORDER_INDEX = {option: index for index, option in enumerate(OPTION_ORDER)}
CRITERIA = ("s_land", "s_water", "s_practice")
BOOL_COLUMNS = {
    "master_cell.csv": ("is_farm_cell", "two_seasons"),
    "scores_all.csv": ("suit_filled", "water_filled"),
    "recommendations.csv": ("is_farm_cell",),
}
REQUIRED_COLUMNS = {
    "master_cell.csv": {
        "cell_id",
        "row",
        "col",
        "lat",
        "lon",
        "farm_pct",
        "is_farm_cell",
    },
    "scores_all.csv": {
        "cell_id",
        "option",
        "winter_crop",
        "summer_crop",
        "suitability",
        "irrig_mm_year",
        "practice_pct",
        *CRITERIA,
        "score_fit",
        "score_water",
        "rank_fit",
        "rank_water",
        "suit_filled",
        "water_filled",
        "reason",
    },
    "recommendations.csv": {
        "cell_id",
        "row",
        "col",
        "lat",
        "lon",
        "farm_pct",
        "is_farm_cell",
        "top1_option",
        "top1_score",
        "top1_reason",
        "top2_option",
        "top2_score",
        "top2_reason",
        "top3_option",
        "top3_score",
        "top3_reason",
        "water_alt_option",
        "water_alt_saving_mm",
        "water_alt_saving_m3_ha",
        "water_alt_reason",
        "robustness",
        "winter_robustness",
        "summer_robustness",
        "confidence",
        "warnings",
    },
}


@dataclass(frozen=True)
class DatasetBundle:
    master: pd.DataFrame
    dictionary: pd.DataFrame
    scores: pd.DataFrame
    recommendations: pd.DataFrame
    manifest: dict[str, Any]


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise DataLoadError("Data manifest is missing or invalid.") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise DataLoadError("Data manifest must include file metadata.")
    if (
        not isinstance(manifest.get("source_url"), str)
        or not manifest["source_url"].strip()
        or not isinstance(manifest.get("source_commit"), str)
        or not manifest["source_commit"].strip()
        or manifest.get("option_order") != list(OPTION_ORDER)
    ):
        raise DataLoadError("Data manifest is missing valid source or scoring metadata.")
    return manifest


def _verify_hash(path: Path, expected: str) -> None:
    """Verify the pinned SHA-256 of a source file.

    A Windows git checkout with core.autocrlf=true rewrites LF line endings as
    CRLF. That changes the bytes but not one value in the table, so the file is
    also accepted when its content with CRLF turned back into LF matches the
    pinned hash. Any other difference still fails the check.
    """
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise DataLoadError(f"Unable to read required input {path.name}.") from exc
    expected = str(expected).lower()
    if hashlib.sha256(raw).hexdigest() == expected:
        return
    if b"\r\n" in raw and hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == expected:
        return
    raise DataLoadError(f"Dataset integrity check failed for {path.name}.")


def _parse_boolean_columns(frame: pd.DataFrame, columns: tuple[str, ...], filename: str) -> None:
    for column in columns:
        if column not in frame.columns:
            raise DataLoadError(f"{filename} is missing required column {column}.")
        parsed: list[bool] = []
        for value in frame[column]:
            if isinstance(value, (bool, np.bool_)):
                parsed.append(bool(value))
                continue
            if pd.isna(value):
                raise DataLoadError(f"{filename}.{column} contains a missing Boolean value.")
            normalized = str(value).strip().lower()
            if normalized in {"true", "1"}:
                parsed.append(True)
            elif normalized in {"false", "0"}:
                parsed.append(False)
            else:
                raise DataLoadError(f"{filename}.{column} contains an invalid Boolean value.")
        frame[column] = parsed


def _validate_cell_ids(frame: pd.DataFrame, filename: str) -> set[int]:
    if "cell_id" not in frame.columns:
        raise DataLoadError(f"{filename} is missing required column cell_id.")
    numeric = pd.to_numeric(frame["cell_id"], errors="coerce")
    values = numeric.to_numpy(dtype=float, na_value=np.nan)
    if (
        not np.isfinite(values).all()
        or not np.equal(values, np.floor(values)).all()
    ):
        raise DataLoadError(f"{filename}.cell_id must contain finite integer values.")
    frame["cell_id"] = numeric.astype("int64")
    if frame["cell_id"].duplicated().any() and filename != "scores_all.csv":
        raise DataLoadError(f"{filename}.cell_id values must be unique.")
    return set(frame["cell_id"].tolist())


def _numeric_column(frame: pd.DataFrame, column: str, filename: str, allow_missing: bool) -> None:
    original = frame[column]
    numeric = pd.to_numeric(original, errors="coerce")
    invalid_text = original.notna() & numeric.isna()
    if invalid_text.any():
        raise DataLoadError(f"{filename}.{column} contains a non-numeric value.")
    values = numeric.to_numpy(dtype=float, na_value=np.nan)
    present = ~np.isnan(values)
    if (not allow_missing and not present.all()) or not np.isfinite(values[present]).all():
        raise DataLoadError(f"{filename}.{column} must contain finite numeric values.")
    frame[column] = numeric


def _read_csv(data_dir: Path, filename: str) -> pd.DataFrame:
    path = data_dir / filename
    if not path.is_file():
        raise DataLoadError(f"Required input {filename} is missing.")
    try:
        return pd.read_csv(path, low_memory=False)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        raise DataLoadError(f"Unable to parse required input {filename}.") from exc


def load_datasets(data_dir: Path, manifest_path: Path) -> DatasetBundle:
    manifest = _read_manifest(manifest_path)
    file_manifest = manifest["files"]
    frames: dict[str, pd.DataFrame] = {}
    for filename in REQUIRED_FILES:
        metadata = file_manifest.get(filename)
        if not isinstance(metadata, dict) or not metadata.get("sha256"):
            raise DataLoadError(f"Data manifest has no SHA-256 entry for {filename}.")
        input_path = data_dir / filename
        if not input_path.is_file():
            raise DataLoadError(f"Required input {filename} is missing.")
        _verify_hash(input_path, metadata["sha256"])
        frame = _read_csv(data_dir, filename)
        if metadata.get("rows") != len(frame) or metadata.get("columns") != len(frame.columns):
            raise DataLoadError(f"Dataset dimensions do not match the manifest for {filename}.")
        frames[filename] = frame

    master = frames["master_cell.csv"]
    dictionary = frames["master_cell_dictionary.csv"]
    scores = frames["scores_all.csv"]
    recommendations = frames["recommendations.csv"]

    for filename, required_columns in REQUIRED_COLUMNS.items():
        missing = sorted(required_columns - set(frames[filename].columns))
        if missing:
            raise DataLoadError(
                f"{filename} is missing required columns: {', '.join(missing)}."
            )

    master_ids = _validate_cell_ids(master, "master_cell.csv")
    score_ids = _validate_cell_ids(scores, "scores_all.csv")
    recommendation_ids = _validate_cell_ids(recommendations, "recommendations.csv")
    if score_ids != master_ids or recommendation_ids != master_ids:
        raise DataLoadError("Cell ID sets do not match across the three data tables.")

    if scores.duplicated(["cell_id", "option"]).any():
        raise DataLoadError("scores_all.csv contains duplicate cell_id/option keys.")
    if set(scores["option"].dropna().unique()) != set(OPTION_ORDER):
        raise DataLoadError("scores_all.csv does not contain the expected 13 rotation options.")
    counts = scores.groupby("cell_id", sort=False)["option"].nunique()
    if not counts.eq(len(OPTION_ORDER)).all():
        raise DataLoadError("Every cell must have all 13 distinct rotation options.")
    if len(scores) != len(master) * len(OPTION_ORDER):
        raise DataLoadError("scores_all.csv must contain exactly 13 options per cell.")

    for column in (*CRITERIA, "score_fit", "score_water"):
        _numeric_column(scores, column, "scores_all.csv", allow_missing=False)
        if not scores[column].between(0, 1).all():
            raise DataLoadError(f"scores_all.csv.{column} must be between 0 and 1.")
    for column in ("rank_fit", "rank_water"):
        _numeric_column(scores, column, "scores_all.csv", allow_missing=False)
        if not scores[column].eq(np.floor(scores[column])).all():
            raise DataLoadError(f"scores_all.csv.{column} must contain integer ranks.")
    _numeric_column(scores, "irrig_mm_year", "scores_all.csv", allow_missing=True)
    if (scores["irrig_mm_year"].dropna() < 0).any():
        raise DataLoadError("scores_all.csv.irrig_mm_year must be nonnegative.")

    irrigation_columns = [
        column
        for column in master.columns
        if column.startswith(("irrig_mm_", "irrig_need_"))
    ]
    for column in irrigation_columns:
        _numeric_column(master, column, "master_cell.csv", allow_missing=True)
        if (master[column].dropna() < 0).any():
            raise DataLoadError(f"master_cell.csv.{column} must be nonnegative.")

    if "column" not in dictionary.columns or dictionary["column"].duplicated().any():
        raise DataLoadError("master_cell_dictionary.csv must uniquely define each column.")
    dictionary_columns = set(dictionary["column"].dropna().astype(str))
    uncovered = sorted(set(master.columns) - dictionary_columns)
    if uncovered:
        raise DataLoadError(
            "master_cell_dictionary.csv does not cover master_cell.csv columns: "
            + ", ".join(uncovered)
            + "."
        )

    for filename, columns in BOOL_COLUMNS.items():
        _parse_boolean_columns(frames[filename], columns, filename)
    master_eligibility = master.set_index("cell_id")["is_farm_cell"]
    recommendation_eligibility = recommendations.set_index("cell_id")[
        "is_farm_cell"
    ].reindex(master["cell_id"].tolist())
    if not master_eligibility.equals(recommendation_eligibility):
        raise DataLoadError("Farm eligibility does not match between the cell and recommendation tables.")
    nonfarm = set(master.loc[~master["is_farm_cell"], "cell_id"])
    recommendation_columns = [
        column
        for column in recommendations.columns
        if column.startswith(("top", "water_alt"))
    ]
    if nonfarm and recommendations.set_index("cell_id").loc[
        sorted(nonfarm), recommendation_columns
    ].notna().any().any():
        raise DataLoadError("Non-farm cells must not have published recommendations.")
    for column in ("top1_score", "top2_score", "top3_score"):
        _numeric_column(recommendations, column, "recommendations.csv", allow_missing=True)
        if not recommendations.loc[recommendations["is_farm_cell"], column].between(0, 1).all():
            raise DataLoadError(f"recommendations.csv.{column} must be between 0 and 1.")
    for column in ("robustness", "winter_robustness", "summer_robustness"):
        _numeric_column(recommendations, column, "recommendations.csv", allow_missing=False)
        if not recommendations[column].between(0, 1).all():
            raise DataLoadError(f"recommendations.csv.{column} must be between 0 and 1.")

    farm_recommendations = recommendations.loc[recommendations["is_farm_cell"]]
    required_published_fields = [
        "top1_option",
        "top1_score",
        "top1_reason",
        "top2_option",
        "top2_score",
        "top2_reason",
        "top3_option",
        "top3_score",
        "top3_reason",
        "water_alt_option",
        "water_alt_reason",
        "confidence",
    ]
    if farm_recommendations[required_published_fields].isna().any().any():
        raise DataLoadError("Farm cells must have all published default recommendations.")

    return DatasetBundle(master, dictionary, scores, recommendations, manifest)


def to_json_value(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if pd.isna(value):
        return None
    return value


def row_to_json(row: pd.Series) -> dict[str, Any]:
    return {str(key): to_json_value(value) for key, value in row.items()}
