from typing import Any

import pandas as pd

from app.repositories.csv_repository import DatasetBundle, row_to_json, to_json_value


class CellService:
    def __init__(self, datasets: DatasetBundle):
        self.datasets = datasets
        self._master = datasets.master.set_index("cell_id", drop=False)
        self._recommendations = datasets.recommendations.set_index("cell_id", drop=False)
        self._scores = datasets.scores.set_index("cell_id", drop=False)

    def _cell(self, cell_id: int) -> pd.Series | None:
        if cell_id not in self._master.index:
            return None
        return self._master.loc[cell_id]

    def list_cells(self) -> list[dict[str, Any]]:
        return [
            {
                "cell_id": int(row.cell_id),
                "row": to_json_value(row["row"]),
                "col": to_json_value(row["col"]),
                "lat": to_json_value(row["lat"]),
                "lon": to_json_value(row["lon"]),
                "farmland_share": to_json_value(row["farm_pct"]),
                "farm_eligible": bool(row["is_farm_cell"]),
            }
            for _, row in self.datasets.master.iterrows()
        ]

    def get_profile(self, cell_id: int) -> dict[str, Any] | None:
        cell = self._cell(cell_id)
        return row_to_json(cell) if cell is not None else None

    def get_recommendations(self, cell_id: int) -> dict[str, Any] | None:
        cell = self._cell(cell_id)
        if cell is None:
            return None
        eligible = bool(cell["is_farm_cell"])
        published = self._recommendations.loc[cell_id]
        if not eligible:
            return {
                "cell_id": cell_id,
                "farm_eligible": False,
                "recommendations": [],
                "water_alternative": None,
                "published_default_analysis": self._confidence(published),
                "warnings": self._warnings(published),
            }

        options = []
        for rank in (1, 2, 3):
            options.append(
                {
                    "rank": rank,
                    "option": published[f"top{rank}_option"],
                    "score": to_json_value(published[f"top{rank}_score"]),
                    "reason": published[f"top{rank}_reason"],
                }
            )
        score_rows = self._scores.loc[cell_id].set_index("option")
        top_irrigation = to_json_value(
            score_rows.loc[options[0]["option"], "irrig_mm_year"]
        )
        alternative_name = published["water_alt_option"]
        alternative_score = score_rows.loc[alternative_name]
        alternative_irrigation = to_json_value(alternative_score["irrig_mm_year"])
        difference = (
            top_irrigation - alternative_irrigation
            if top_irrigation is not None and alternative_irrigation is not None
            else None
        )
        return {
            "cell_id": cell_id,
            "farm_eligible": True,
            "recommendations": options,
            "water_alternative": {
                "option": alternative_name,
                "reason": published["water_alt_reason"],
                "irrig_mm_year": alternative_irrigation,
                "modeled_irrigation_difference_mm_year": difference,
                "modeled_irrigation_difference_m3_ha_year": (
                    difference * 10 if difference is not None else None
                ),
                "difference_definition": "default top option minus water alternative",
            },
            "published_default_analysis": self._confidence(published),
            "warnings": self._warnings(published),
        }

    @staticmethod
    def _warnings(row: pd.Series) -> list[str]:
        value = row["warnings"]
        return [warning for warning in str(value).split(" | ") if warning] if pd.notna(value) else []

    @staticmethod
    def _confidence(row: pd.Series) -> dict[str, Any]:
        return {
            "label": to_json_value(row["confidence"]),
            "robustness": to_json_value(row["robustness"]),
            "winter_robustness": to_json_value(row["winter_robustness"]),
            "summer_robustness": to_json_value(row["summer_robustness"]),
            "basis": "Published default notebook analysis; not recalculated for custom weights.",
        }
