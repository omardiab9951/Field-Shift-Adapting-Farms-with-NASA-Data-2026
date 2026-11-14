from typing import Any

import pandas as pd

from app.repositories.csv_repository import (
    CRITERIA,
    OPTION_ORDER,
    OPTION_ORDER_INDEX,
    DatasetBundle,
    to_json_value,
)


class ScoringService:
    def __init__(self, datasets: DatasetBundle):
        self.datasets = datasets
        self._master = datasets.master.set_index("cell_id", drop=False)
        self._scores = datasets.scores.set_index("cell_id", drop=False)
        self._recommendations = datasets.recommendations.set_index("cell_id", drop=False)

    def _cell(self, cell_id: int) -> pd.Series | None:
        if cell_id not in self._master.index:
            return None
        return self._master.loc[cell_id]

    def get_scores(self, cell_id: int) -> dict[str, Any] | None:
        if self._cell(cell_id) is None:
            return None
        rows = self._scores.loc[cell_id].set_index("option", drop=False)
        return {
            "cell_id": cell_id,
            "farm_eligible": bool(self._master.loc[cell_id, "is_farm_cell"]),
            "options": [
                self._score_record(rows.loc[option], rank=None)
                for option in OPTION_ORDER
            ],
        }

    def evaluate(
        self, cell_id: int, weights: dict[str, float]
    ) -> dict[str, Any] | None:
        cell = self._cell(cell_id)
        if cell is None:
            return None
        normalized = normalize_weights(weights)
        if not bool(cell["is_farm_cell"]):
            return {
                "cell_id": cell_id,
                "farm_eligible": False,
                "result": "not_eligible",
                "normalized_weights": normalized,
                "ranked_options": [],
                "top_three": [],
                "land_water_alternative": None,
                "modeled_irrigation_difference": None,
                "published_default_analysis": self._published_default(cell_id),
            }

        cell_scores = self._scores.loc[cell_id]
        weight_scale = max(weights.values())
        scaled_weights = {
            name: value / weight_scale for name, value in weights.items()
        }
        scaled_total = sum(scaled_weights.values())
        evaluated = []
        for _, row in cell_scores.iterrows():
            components = {name: float(row[name]) for name in CRITERIA}
            weighted = {
                name: normalized[weight_name] * components[component_name]
                for name, weight_name, component_name in (
                    ("land", "land", "s_land"),
                    ("water", "water", "s_water"),
                    ("practice", "practice", "s_practice"),
                )
            }
            score = sum(
                scaled_weights[name] * components[component_name]
                for name, component_name in (
                    ("land", "s_land"),
                    ("water", "s_water"),
                    ("practice", "s_practice"),
                )
            ) / scaled_total
            evaluated.append(
                self._evaluation_record(row, score, weighted, rank=0)
            )
        ranked = rank_options(evaluated)
        for rank, record in enumerate(ranked, start=1):
            record["rank"] = rank

        alternative_weights = {"land": 1.0, "water": 1.0, "practice": 0.0}
        alternative_norm = normalize_weights(alternative_weights)
        alternative_candidates = []
        for _, row in cell_scores.iterrows():
            components = {name: float(row[name]) for name in CRITERIA}
            score = (components["s_land"] + components["s_water"]) / 2
            alternative_candidates.append(
                self._evaluation_record(
                    row,
                    score,
                    {
                        "land": alternative_norm["land"] * components["s_land"],
                        "water": alternative_norm["water"] * components["s_water"],
                        "practice": 0.0,
                    },
                    rank=0,
                )
            )
        alternative = rank_options(alternative_candidates)[0]
        custom_top = ranked[0]
        irrigation_difference = (
            alternative["irrig_mm_year"] - custom_top["irrig_mm_year"]
            if alternative["irrig_mm_year"] is not None
            and custom_top["irrig_mm_year"] is not None
            else None
        )
        alternative["rank"] = 1
        alternative["weights"] = alternative_norm
        return {
            "cell_id": cell_id,
            "farm_eligible": True,
            "result": "evaluated",
            "normalized_weights": normalized,
            "ranked_options": ranked,
            "top_three": ranked[:3],
            "land_water_alternative": alternative,
            "modeled_irrigation_difference": {
                "reference": "land-water alternative minus custom top option",
                "mm_year": irrigation_difference,
                "m3_ha_year": (
                    irrigation_difference * 10
                    if irrigation_difference is not None
                    else None
                ),
            },
            "published_default_analysis": self._published_default(cell_id),
        }

    @staticmethod
    def _score_record(row: pd.Series, rank: int | None) -> dict[str, Any]:
        record = {
            "option": row["option"],
            "winter_crop": to_json_value(row["winter_crop"]),
            "summer_crop": to_json_value(row["summer_crop"]),
            "suitability": to_json_value(row["suitability"]),
            "irrig_mm_year": to_json_value(row["irrig_mm_year"]),
            "practice_pct": to_json_value(row["practice_pct"]),
            "components": {name: to_json_value(row[name]) for name in CRITERIA},
            "published_equal_weight_score": to_json_value(row["score_fit"]),
            "published_land_water_score": to_json_value(row["score_water"]),
            "published_rank_equal_weight": to_json_value(row["rank_fit"]),
            "published_rank_land_water": to_json_value(row["rank_water"]),
            "suit_filled": bool(row["suit_filled"]),
            "water_filled": bool(row["water_filled"]),
            "reason": to_json_value(row["reason"]),
        }
        if rank is not None:
            record["rank"] = rank
        return record

    @classmethod
    def _evaluation_record(
        cls,
        row: pd.Series,
        score: float,
        contributions: dict[str, float],
        rank: int,
    ) -> dict[str, Any]:
        record = cls._score_record(row, rank)
        record.update(
            {
                "score": score,
                "weighted_contributions": contributions,
                "irrig_m3_ha_year": (
                    float(row["irrig_mm_year"]) * 10
                    if pd.notna(row["irrig_mm_year"])
                    else None
                ),
            }
        )
        return record

    def _published_default(self, cell_id: int) -> dict[str, Any]:
        row = self._recommendations.loc[cell_id]
        return {
            "confidence": to_json_value(row["confidence"]),
            "robustness": to_json_value(row["robustness"]),
            "winter_robustness": to_json_value(row["winter_robustness"]),
            "summer_robustness": to_json_value(row["summer_robustness"]),
            "basis": "Published default notebook analysis; not custom-weight confidence or probability.",
        }


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    scale = max(weights.values())
    scaled = {name: value / scale for name, value in weights.items()}
    total = sum(scaled.values())
    return {name: value / total for name, value in scaled.items()}


def rank_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        options,
        key=lambda item: (-item["score"], OPTION_ORDER_INDEX[item["option"]]),
    )
