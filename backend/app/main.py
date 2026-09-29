"""DocumentTrust India — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure runtime directories exist on startup."""
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.heatmap_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-based Fake Identity & Document Screening System — API",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.mount(
        settings.static_uploads_prefix,
        StaticFiles(directory=str(settings.upload_dir)),
        name="uploads",
    )
    application.mount(
        settings.static_heatmaps_prefix,
        StaticFiles(directory=str(settings.heatmap_dir)),
        name="heatmaps",
    )

    application.include_router(api_router, prefix="/api/v1")

    @application.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "service": settings.app_name}

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
