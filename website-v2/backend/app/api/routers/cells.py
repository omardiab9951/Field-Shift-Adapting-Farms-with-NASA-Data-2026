from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import require_datasets
from app.repositories.csv_repository import DatasetBundle
from app.services.cell_service import CellService
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/api", tags=["cells"])


@router.get("/cells")
def list_cells(datasets: DatasetBundle = Depends(require_datasets)):
    return CellService(datasets).list_cells()


@router.get("/cells/{cell_id}")
def get_cell(cell_id: int, datasets: DatasetBundle = Depends(require_datasets)):
    profile = CellService(datasets).get_profile(cell_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown cell ID.")
    return profile


@router.get("/cells/{cell_id}/recommendations")
def get_recommendations(
    cell_id: int, datasets: DatasetBundle = Depends(require_datasets)
):
    result = CellService(datasets).get_recommendations(cell_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown cell ID.")
    return result


@router.get("/cells/{cell_id}/scores")
def get_scores(cell_id: int, datasets: DatasetBundle = Depends(require_datasets)):
    result = ScoringService(datasets).get_scores(cell_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown cell ID.")
    return result
