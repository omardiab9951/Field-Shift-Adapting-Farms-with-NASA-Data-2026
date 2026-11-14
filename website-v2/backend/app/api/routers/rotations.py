from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import require_datasets
from app.repositories.csv_repository import DatasetBundle
from app.schemas.rotations import RotationEvaluationRequest
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/api/rotations", tags=["rotations"])


@router.post("/evaluate")
def evaluate_rotation(
    request: RotationEvaluationRequest,
    datasets: DatasetBundle = Depends(require_datasets),
):
    result = ScoringService(datasets).evaluate(
        request.cell_id, request.weights.model_dump()
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown cell ID.")
    return result
