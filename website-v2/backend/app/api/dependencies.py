from fastapi import HTTPException, Request, status

from app.repositories.csv_repository import DatasetBundle


def require_datasets(request: Request) -> DatasetBundle:
    datasets = getattr(request.app.state, "datasets", None)
    if datasets is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "data_not_ready",
                "message": getattr(
                    request.app.state,
                    "data_error",
                    "Dataset validation has not completed.",
                ),
            },
        )
    return datasets
