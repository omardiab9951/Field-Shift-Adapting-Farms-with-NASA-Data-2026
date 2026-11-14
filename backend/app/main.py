from contextlib import asynccontextmanager

from fastapi import FastAPI

from .data_loader import MasterDataset, load_master_dataset


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load and validate the integrated dataset before serving requests."""
    dataset = load_master_dataset()
    app.state.master_dataset = dataset
    yield
    app.state.master_dataset = None


app = FastAPI(
    title="Field Shift API",
    version="0.1.0",
    description="Backend foundation for the NASA-powered crop-rotation decision tool.",
    lifespan=lifespan,
)


@app.get("/api/health")
def health() -> dict[str, object]:
    """Return service status after startup validation succeeds."""
    dataset: MasterDataset = app.state.master_dataset
    return {
        "status": "ok",
        "dataset": {
            "path": str(dataset.path),
            "rows": len(dataset.frame),
            "columns": len(dataset.frame.columns),
            "cells": int(dataset.frame["cell_id"].nunique()),
            "periods": int(dataset.frame[["year", "month"]].drop_duplicates().shape[0]),
        },
    }
