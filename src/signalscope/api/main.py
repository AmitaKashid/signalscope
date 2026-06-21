"""ASGI entry point for the SignalScope backend."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from signalscope.api.container import build_container
from signalscope.api.routes import approvals, assets, campaigns, evaluations, health
from signalscope.core.config import get_settings
from signalscope.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize configuration and warm in-memory catalog indexes."""

    settings = get_settings()
    configure_logging(settings)
    container = build_container(settings)
    container.catalog.load()
    app.state.container = container
    logger = get_logger("signalscope.api", environment=settings.environment)
    logger.info(
        "application_started", extra={"catalog_assets": len(container.catalog.list_assets())}
    )
    yield
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """Create a configured FastAPI application."""

    app = FastAPI(
        title="SignalScope API",
        summary="Explainable multimodal media intelligence workflow API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    app.include_router(health.router)
    app.include_router(assets.router)
    app.include_router(campaigns.router)
    app.include_router(approvals.router)
    app.include_router(evaluations.router)
    return app


app = create_app()


def run() -> None:
    """Run the API using settings appropriate for local development."""

    uvicorn.run("signalscope.api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
