import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core.config import BACKEND_DIR, DATA_DIR, MANIFEST_PATH
from app.main import create_app
from app.repositories.csv_repository import OPTION_ORDER
from app.services.scoring_service import ScoringService, rank_options


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def local_temp_dir():
    with tempfile.TemporaryDirectory(
        prefix="fieldshift-test-", dir=BACKEND_DIR
    ) as directory:
        yield Path(directory)


def _copy_inputs(directory: Path) -> tuple[Path, Path]:
    directory.mkdir()
    for filename in (
        "master_cell.csv",
        "master_cell_dictionary.csv",
        "scores_all.csv",
        "recommendations.csv",
    ):
        shutil.copyfile(DATA_DIR / filename, directory / filename)
    manifest_path = directory / "manifest.json"
    shutil.copyfile(MANIFEST_PATH, manifest_path)
    return directory, manifest_path


def test_health_and_actual_data_dimensions(client: TestClient):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["data_ready"] is True

    data_info = client.get("/api/data-info").json()
    assert data_info["source_commit"] == "930ced44d013ac5760b38fee035fea9f5738b657"
    assert data_info["datasets"] == {
        "master_cell": {"rows": 560, "columns": 189},
        "master_cell_dictionary": {"rows": 189, "columns": 6},
        "scores_all": {"rows": 7280, "columns": 17},
        "recommendations": {"rows": 560, "columns": 25},
    }
    assert any("Rice net irrigation excludes" in item for item in data_info["limitations"])


def test_missing_and_invalid_data_keep_health_available(local_temp_dir: Path):
    tmp_path = local_temp_dir
    missing_dir = tmp_path / "missing"
    missing_dir.mkdir()
    missing_client = TestClient(create_app(missing_dir, MANIFEST_PATH))
    with missing_client:
        health = missing_client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["data_ready"] is False
        assert missing_client.get("/api/cells").status_code == 503

    invalid_dir, manifest_path = _copy_inputs(tmp_path / "invalid")
    scores_path = invalid_dir / "scores_all.csv"
    scores = pd.read_csv(scores_path)
    scores.loc[0, "s_land"] = 1.25
    scores.to_csv(scores_path, index=False)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["scores_all.csv"]["sha256"] = hashlib.sha256(
        scores_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    invalid_client = TestClient(create_app(invalid_dir, manifest_path))
    with invalid_client:
        health = invalid_client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["data_ready"] is False
        assert "between 0 and 1" in health.json()["data_error"]
        assert invalid_client.get("/api/data-info").status_code == 503


def test_unknown_cells_and_invalid_weights(client: TestClient):
    assert client.get("/api/cells/99999").status_code == 404
    assert client.get("/api/cells/99999/scores").status_code == 404
    payload = {"cell_id": 1, "weights": {"land": 0, "water": 0, "practice": 0}}
    assert client.post("/api/rotations/evaluate", json=payload).status_code == 422
    payload["weights"] = {"land": -1, "water": 1, "practice": 1}
    assert client.post("/api/rotations/evaluate", json=payload).status_code == 422
    payload["weights"] = {"land": 1, "water": 1}
    assert client.post("/api/rotations/evaluate", json=payload).status_code == 422
    payload["weights"] = {"land": float("inf"), "water": 1, "practice": 1}
    response = client.post(
        "/api/rotations/evaluate",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    payload["weights"] = {"land": 1, "water": 1, "practice": 1}
    payload["cell_id"] = 1.5
    assert client.post("/api/rotations/evaluate", json=payload).status_code == 422
    payload["cell_id"] = 99999
    assert client.post("/api/rotations/evaluate", json=payload).status_code == 404


def test_nonfarm_recommendations_are_suppressed(client: TestClient):
    profile = client.get("/api/cells/69").json()
    assert profile["is_farm_cell"] is False
    scores = client.get("/api/cells/69/scores").json()
    assert scores["farm_eligible"] is False
    assert len(scores["options"]) == 13
    recommendations = client.get("/api/cells/69/recommendations").json()
    assert recommendations["farm_eligible"] is False
    assert recommendations["recommendations"] == []
    assert recommendations["water_alternative"] is None

    result = client.post(
        "/api/rotations/evaluate",
        json={
            "cell_id": 69,
            "weights": {"land": 1, "water": 1, "practice": 1},
        },
    ).json()
    assert result["result"] == "not_eligible"
    assert result["ranked_options"] == []
    assert result["top_three"] == []
    assert result["land_water_alternative"] is None


def test_equal_weight_scores_and_default_recommendations_match_csv(client: TestClient):
    datasets = client.app.state.datasets
    service = ScoringService(datasets)
    published_scores = datasets.scores.set_index(["cell_id", "option"])
    recommendations = datasets.recommendations.set_index("cell_id")
    farm_cells = datasets.master.loc[
        datasets.master["is_farm_cell"], "cell_id"
    ].tolist()

    for cell_id in farm_cells:
        evaluation = service.evaluate(
            int(cell_id), {"land": 1, "water": 1, "practice": 1}
        )
        ranked = evaluation["ranked_options"]
        assert len(ranked) == 13
        for item in ranked:
            published = published_scores.loc[(cell_id, item["option"])]
            assert item["rank"] == int(published["rank_fit"])
            assert item["score"] == pytest.approx(
                published["score_fit"], abs=1e-12
            )

        recommendation = recommendations.loc[cell_id]
        for rank in (1, 2, 3):
            item = ranked[rank - 1]
            assert item["option"] == recommendation[f"top{rank}_option"]
            assert round(item["score"], 3) == pytest.approx(
                recommendation[f"top{rank}_score"], abs=0.0005
            )


def test_land_water_priority_matches_published_rankings(client: TestClient):
    datasets = client.app.state.datasets
    service = ScoringService(datasets)
    published_scores = datasets.scores.set_index(["cell_id", "option"])
    farm_cells = datasets.master.loc[
        datasets.master["is_farm_cell"], "cell_id"
    ].tolist()

    for cell_id in farm_cells:
        evaluation = service.evaluate(
            int(cell_id), {"land": 1, "water": 1, "practice": 0}
        )
        for item in evaluation["ranked_options"]:
            published = published_scores.loc[(cell_id, item["option"])]
            assert item["rank"] == int(published["rank_water"])
            assert item["score"] == pytest.approx(
                published["score_water"], abs=1e-12
            )


def test_option_ties_follow_notebook_order():
    options = [
        {"option": option, "score": 0.5}
        for option in reversed(OPTION_ORDER)
    ]
    assert [item["option"] for item in rank_options(options)] == list(OPTION_ORDER)


def test_missing_profile_values_are_strict_json_nulls(client: TestClient):
    master = client.app.state.datasets.master
    row = master.loc[master["irrig_mm_wheat"].isna()].iloc[0]
    response = client.get(f"/api/cells/{int(row['cell_id'])}")
    assert response.status_code == 200

    def reject_constant(value: str):
        raise AssertionError(f"Non-standard JSON constant: {value}")

    profile = json.loads(response.content, parse_constant=reject_constant)
    assert profile["irrig_mm_wheat"] is None


def test_evaluate_returns_signed_irrigation_difference_and_components(client: TestClient):
    result = client.post(
        "/api/rotations/evaluate",
        json={"cell_id": 1, "weights": {"land": 1, "water": 1, "practice": 1}},
    ).json()
    assert sum(result["normalized_weights"].values()) == pytest.approx(1)
    assert len(result["ranked_options"]) == 13
    top = result["ranked_options"][0]
    assert top["score"] == pytest.approx(
        sum(top["weighted_contributions"].values())
    )
    difference = result["modeled_irrigation_difference"]
    expected = (
        result["land_water_alternative"]["irrig_mm_year"]
        - top["irrig_mm_year"]
    )
    assert difference["mm_year"] == pytest.approx(expected)
    assert difference["m3_ha_year"] == pytest.approx(expected * 10)
    assert result["published_default_analysis"]["basis"].startswith("Published default")


def test_data_info_and_cell_list_are_available(client: TestClient):
    cells = client.get("/api/cells").json()
    assert len(cells) == 560
    assert set(cells[0]) == {
        "cell_id",
        "row",
        "col",
        "lat",
        "lon",
        "farmland_share",
        "farm_eligible",
    }


def test_cors_is_limited_to_the_existing_frontend_origins(client: TestClient):
    allowed = client.options(
        "/api/cells",
        headers={
            "Origin": "http://127.0.0.1:8080",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:8080"

    rejected = client.options(
        "/api/cells",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in rejected.headers
