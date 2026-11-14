import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import cells, health, rotations, dashboard
from app.core.config import ALLOWED_ORIGINS, DATA_DIR, HOST, MANIFEST_PATH, PORT
from app.core.errors import DataLoadError
from app.repositories.csv_repository import load_datasets

logger = logging.getLogger("field_shift")


def create_app(data_dir: Path = DATA_DIR, manifest_path: Path = MANIFEST_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.datasets = None
        application.state.data_error = None
        try:
            application.state.datasets = load_datasets(data_dir, manifest_path)
        except DataLoadError as exc:
            application.state.data_error = str(exc)
            logger.error("Dataset readiness check failed: %s", exc)
        yield

    application = FastAPI(
        title="Field Shift API",
        description="Local API for the pinned Field Shift Final-System datasets.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "loc": list(error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors})

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(ALLOWED_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.include_router(health.router)
    application.include_router(cells.router)
    application.include_router(rotations.router)
    application.include_router(dashboard.router)
    website = Path(__file__).resolve().parents[2]
    application.mount("/css", StaticFiles(directory=website / "css"), name="css")
    application.mount("/js", StaticFiles(directory=website / "js"), name="js")

    @application.get("/", include_in_schema=False)
    def frontend():
        return FileResponse(website / "index.html", headers={"Cache-Control": "no-cache"})

    @application.get("/favicon.ico", include_in_schema=False)
    def favicon():
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect width="24" height="24" rx="6" fill="#345745"/>'
               '<path d="M12 20V11M12 14c-6 1-7-6-7-6s6-1 7 6Zm0-4c0-6 7-7 7-7s1 8-7 7Z" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/></svg>')
        return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": "max-age=86400"})

    @application.get("/story.html", include_in_schema=False)
    def story():
        return FileResponse(website / "story.html")

    return application


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
