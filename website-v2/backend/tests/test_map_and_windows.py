"""Map grid geometry, Windows checkouts and the static assets the map needs."""
import shutil
from math import cos, radians

import pytest
from fastapi.testclient import TestClient

from app.core.config import DATA_DIR, MANIFEST_PATH
from app.core.errors import DataLoadError
from app.main import create_app
from app.repositories.csv_repository import load_datasets


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app()) as c:
        yield c


def test_grid_has_every_cell_with_its_corners(client):
    data = client.get("/api/dashboard/catalog").json()
    grid = data["grid"]
    assert len(grid) == 560
    assert sum(c["is_farm"] for c in grid) == 556
    farm_ids = {c["id"] for c in data["cells"]}
    assert {c["id"] for c in grid if c["is_farm"]} == farm_ids
    for c in grid:
        lats = [p[0] for p in c["corners"]]
        lons = [p[1] for p in c["corners"]]
        # the cell centre sits inside its own corners
        assert min(lats) < c["lat"] < max(lats)
        assert min(lons) < c["lon"] < max(lons)
        # each side is about 1 km
        height_m = (max(lats) - min(lats)) * 111_320
        width_m = (max(lons) - min(lons)) * 111_320 * cos(radians(c["lat"]))
        assert 950 < height_m < 1_060 and 950 < width_m < 1_060


def test_neighbouring_cells_share_a_corner(client):
    grid = {(c["row"], c["col"]): c for c in client.get("/api/dashboard/catalog").json()["grid"]}
    a, b = grid[(10, 10)], grid[(10, 11)]
    # top-right of a == top-left of b, to well under a metre
    assert abs(a["corners"][1][0] - b["corners"][0][0]) < 1e-5
    assert abs(a["corners"][1][1] - b["corners"][0][1]) < 1e-5


def test_windows_crlf_checkout_still_loads(tmp_path):
    data_dir = tmp_path / "processed"
    shutil.copytree(DATA_DIR, data_dir)
    for csv in data_dir.glob("*.csv"):
        csv.write_bytes(csv.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    bundle = load_datasets(data_dir, MANIFEST_PATH)
    assert len(bundle.master) == 560


def test_a_changed_value_still_fails_the_check(tmp_path):
    data_dir = tmp_path / "processed"
    shutil.copytree(DATA_DIR, data_dir)
    target = data_dir / "master_cell.csv"
    raw = target.read_bytes()
    target.write_bytes(raw.replace(b"31.", b"32.", 1))
    with pytest.raises(DataLoadError):
        load_datasets(data_dir, MANIFEST_PATH)


def test_match_explains_why_a_point_is_rejected(client):
    far = client.post("/api/dashboard/match", json={"lat": 30.0, "lon": 31.0})
    assert far.status_code == 422 and far.json()["detail"]["code"] == "outside_coverage"


@pytest.mark.parametrize("path", ["/", "/story.html", "/favicon.ico", "/js/vendor/leaflet.js",
                                  "/css/vendor/leaflet.css", "/js/field-map.js"])
def test_pages_and_map_assets_are_served(client, path):
    assert client.get(path).status_code == 200
