from fastapi import APIRouter, Depends, Request

from app.api.dependencies import require_datasets
from app.core.config import LIMITATIONS, SCORING_METHOD
from app.repositories.csv_repository import DatasetBundle

router = APIRouter(prefix="/api", tags=["health and information"])


@router.get("/health")
def health(request: Request):
    # This route intentionally does not depend on dataset readiness.
    datasets = getattr(request.app.state, "datasets", None)
    return {
        "status": "ok",
        "data_ready": datasets is not None,
        "data_error": getattr(request.app.state, "data_error", None),
    }


@router.get("/data-info")
def data_info(datasets: DatasetBundle = Depends(require_datasets)):
    frames = {
        "master_cell": datasets.master,
        "master_cell_dictionary": datasets.dictionary,
        "scores_all": datasets.scores,
        "recommendations": datasets.recommendations,
    }
    return {
        "source_url": datasets.manifest["source_url"],
        "source_commit": datasets.manifest["source_commit"],
        "datasets": {
            name: {"rows": int(frame.shape[0]), "columns": int(frame.shape[1])}
            for name, frame in frames.items()
        },
        "scoring_methodology": SCORING_METHOD,
        "option_order": list(datasets.manifest["option_order"]),
        "limitations": LIMITATIONS,
    }
