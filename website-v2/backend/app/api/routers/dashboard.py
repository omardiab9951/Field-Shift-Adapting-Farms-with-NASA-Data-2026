"""Dashboard contracts backed exclusively by the validated dataset bundle."""
from math import asin, cos, radians, sin, sqrt

import numpy as np

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import require_datasets
from app.repositories.csv_repository import DatasetBundle, to_json_value
from app.schemas.rotations import RotationEvaluationRequest
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# The original project identifies ONE pilot footprint near Sidi Salem and Qallin.
# The CSV has no administrative district membership; do not infer it from midpoints.
STUDY_ID = "sidi-salem-qallin"
STUDY_NAME = {"en": "Sidi Salem & Qallin", "ar": "سيدي سالم وقلين"}


def _grid_geometry(master):
    """Corner coordinates of every 1 km cell.

    The CSV stores cell centres only. Centres lie on a regular UTM 36N grid, so a
    second-order fit of lat/lon on (col, row) reproduces every centre to within
    0.1 m; evaluating it at col +/- 0.5 and row +/- 0.5 gives the cell corners.
    """
    col = master.col.to_numpy(float)
    row = master.row.to_numpy(float)
    def design(c, r):
        return np.column_stack([np.ones_like(c), c, r, c * r, c ** 2, r ** 2])
    a = design(col, row)
    lat_coef = np.linalg.lstsq(a, master.lat.to_numpy(float), rcond=None)[0]
    lon_coef = np.linalg.lstsq(a, master.lon.to_numpy(float), rcond=None)[0]
    cells = []
    for item in master.itertuples():
        c = np.array([item.col - .5, item.col + .5, item.col + .5, item.col - .5], float)
        r = np.array([item.row - .5, item.row - .5, item.row + .5, item.row + .5], float)
        d = design(c, r)
        corners = np.column_stack([d @ lat_coef, d @ lon_coef])
        cells.append({"id": int(item.cell_id), "row": int(item.row), "col": int(item.col),
                      "lat": float(item.lat), "lon": float(item.lon),
                      "is_farm": bool(item.is_farm_cell),
                      "corners": [[round(float(y), 6), round(float(x), 6)] for y, x in corners]})
    return cells


_GRID_CACHE: dict[int, list] = {}


def grid(datasets):
    key = id(datasets)
    if key not in _GRID_CACHE:
        _GRID_CACHE.clear()
        _GRID_CACHE[key] = _grid_geometry(datasets.master)
    return _GRID_CACHE[key]


def catalog(datasets):
    master = datasets.master
    items = [
        {"id": int(row.cell_id), "lat": float(row.lat), "lon": float(row.lon),
         "row": int(row.row), "col": int(row.col), "region_id": STUDY_ID}
        for row in master.loc[master.is_farm_cell].itertuples()
    ]
    center = {"lat": sum(c["lat"] for c in items)/len(items), "lon": sum(c["lon"] for c in items)/len(items)}
    representative = min(items, key=lambda c: (c["lat"]-center["lat"])**2+(c["lon"]-center["lon"])**2)
    return {
        "regions": [{"id": STUDY_ID, "name": STUDY_NAME, "cell_count": len(items),
                     "default_cell": representative["id"], "center": center}],
        "cells": items, "grid": grid(datasets), "source_commit": datasets.manifest["source_commit"],
        "study": {"name": STUDY_NAME, "identity_reference": "Original project presentation, pilot area near Sidi Salem and Qallin",
                  "administrative_boundaries_available": False,
                  "rows": int(master.row.max()), "cols": int(master.col.max())}
    }


class DashboardEvaluationRequest(RotationEvaluationRequest):
    area_feddan: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False, strict=True)


@router.get("/science")
def science(datasets: DatasetBundle = Depends(require_datasets)):
    return {
        "study": catalog(datasets)["study"],
        "cell_count": len(datasets.master),
        "farm_cell_count": int(datasets.master.is_farm_cell.sum()),
        "rotation_count": len(datasets.manifest["option_order"]),
        "source_commit": datasets.manifest["source_commit"],
        "source_url": datasets.manifest["source_url"],
        "methodology_reference": datasets.manifest["methodology_reference"],
        "sources": [{"name": str(name), "field_count": len(group),
                     "fields": [{"column": str(r.column), "description": str(r.description),
                                 "unit": to_json_value(r.unit)} for r in group.itertuples()]}
                    for name, group in datasets.dictionary.groupby("source", sort=False)],
        "criteria": ["s_land", "s_water", "s_practice"],
        "formula": "sum(weight * component) / sum(weights)",
    }


@router.get("/catalog")
def get_catalog(datasets: DatasetBundle = Depends(require_datasets)):
    return catalog(datasets)


@router.post("/evaluate")
def evaluate(payload: DashboardEvaluationRequest, datasets: DatasetBundle = Depends(require_datasets)):
    result = ScoringService(datasets).evaluate(payload.cell_id, payload.weights.model_dump())
    if result is None:
        raise HTTPException(404, "Unknown cell ID.")
    if not result["farm_eligible"]:
        raise HTTPException(422, "This cell is not eligible agricultural land.")
    row = datasets.master.loc[datasets.master.cell_id == payload.cell_id].iloc[0]
    profile = {key: to_json_value(row[key]) for key in ("lat", "lon", "farm_pct", "winter_ndvi", "summer_ndvi", "soil_overall", "rain_mm_year")}
    profile.update(id=payload.cell_id, trend=to_json_value(row.ls_trend_class), ndvi=[to_json_value(row[f"ndvi_m{i:02}"]) for i in range(1,13)])
    profile["monthly"] = [{"month": i, "rain_mm": to_json_value(row[f"rain_mm_m{i:02}"]),
                            "max_temperature_c": to_json_value(row[f"t_max_c_m{i:02}"])} for i in range(1,13)]
    estimates = None
    if payload.area_feddan is not None:
        estimates = {"area_feddan": payload.area_feddan, "feddan_m2": 4200,
                     "rotations": [{"option": option["option"],
                                    "annual_irrigation_m3": option["irrig_mm_year"] * payload.area_feddan * 4.2
                                    if option["irrig_mm_year"] is not None else None}
                                   for option in result["ranked_options"]]}
    return {"profile": profile, "evaluation": result, "farm_estimates": estimates,
            "source_commit": datasets.manifest["source_commit"]}


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    lat: float = Field(ge=-90, le=90, strict=True)
    lon: float = Field(ge=-180, le=180, strict=True)


def distance_m(lat, lon, other_lat, other_lon):
    a = sin(radians(other_lat-lat)/2)**2 + cos(radians(lat))*cos(radians(other_lat))*sin(radians(other_lon-lon)/2)**2
    return 6371000 * 2 * asin(min(1, sqrt(a)))


@router.post("/match")
def match(payload: MatchRequest, datasets: DatasetBundle = Depends(require_datasets)):
    master = datasets.master
    # Reject an out-of-footprint location even when close to a border cell.
    if not (master.lat.min()-.0045 <= payload.lat <= master.lat.max()+.0045 and master.lon.min()-.00525 <= payload.lon <= master.lon.max()+.00525):
        raise HTTPException(422, {"code": "outside_coverage", "message": "Outside study coverage."})
    # Match ALL cells first, so nonfarm cells cannot silently become nearby farms.
    nearest = min(master.itertuples(), key=lambda c: distance_m(payload.lat,payload.lon,c.lat,c.lon))
    distance = distance_m(payload.lat,payload.lon,nearest.lat,nearest.lon)
    if distance > 750 or not nearest.is_farm_cell:
        raise HTTPException(422, {"code": "not_farmland", "message": "No eligible agricultural cell at this location."})
    item = next(c for c in catalog(datasets)["cells"] if c["id"] == nearest.cell_id)
    return {"cell": item, "distance_m": round(distance, 1)}
