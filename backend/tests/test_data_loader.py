import pandas as pd
import pytest

from app.data_loader import DatasetValidationError, load_master_dataset


def valid_frame() -> pd.DataFrame:
    rows = []
    for cell_id in (1, 2):
        for year, month in ((2016, 1), (2016, 2)):
            rows.append(
                {
                    "cell_id": cell_id,
                    "lat": 31.1,
                    "lon": 30.8,
                    "year": year,
                    "month": month,
                    "rain_mm": 20.0,
                }
            )
    return pd.DataFrame(rows)


def test_load_master_dataset_validates_and_loads_csv(tmp_path):
    path = tmp_path / "master_monthly.csv"
    valid_frame().to_csv(path, index=False)

    dataset = load_master_dataset(
        path,
        expected_cell_count=2,
        expected_month_count=2,
    )

    assert len(dataset.frame) == 4
    assert dataset.frame["cell_id"].dtype.kind in "iu"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda frame: frame.drop(columns=["month"]), "missing required columns"),
        (lambda frame: frame.assign(month=0), "month values must be"),
        (lambda frame: pd.concat([frame, frame.iloc[[0]]]), "duplicate"),
        (lambda frame: frame.assign(rain_mm=-999), "fill values"),
    ],
)
def test_load_master_dataset_rejects_invalid_csv(tmp_path, mutation, message):
    path = tmp_path / "master_monthly.csv"
    mutation(valid_frame()).to_csv(path, index=False)

    with pytest.raises(DatasetValidationError, match=message):
        load_master_dataset(
            path,
            expected_cell_count=2,
            expected_month_count=2,
        )


def test_load_master_dataset_rejects_missing_file(tmp_path):
    with pytest.raises(DatasetValidationError, match="Master dataset not found"):
        load_master_dataset(tmp_path / "missing.csv")
