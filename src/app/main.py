from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ExternalApiError
from app.core.handlers import external_api_error_handler
from app.core.logging import configure_logging
from app.core.observability import metrics_middleware


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_exception_handler(ExternalApiError, external_api_error_handler)
    app.middleware("http")(metrics_middleware)
    app.include_router(api_router, prefix=settings.api_prefix)
    app.mount("/metrics", make_asgi_app())
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/", include_in_schema=False)
    async def dashboard() -> FileResponse:
        return FileResponse("frontend/index.html")

    return app


app = create_app()
