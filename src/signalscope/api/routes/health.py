"""Operational health and metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from signalscope.api.container import ApplicationContainer
from signalscope.api.dependencies import get_container

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthcheck(container: ApplicationContainer = Depends(get_container)) -> dict[str, str]:
    """Return a shallow health status suitable for load balancers."""

    return {
        "status": "ok",
        "environment": container.settings.environment,
        "service": "signalscope-api",
    }


@router.get("/readyz")
def readiness(container: ApplicationContainer = Depends(get_container)) -> dict[str, str | int]:
    """Verify that demo catalog data can be loaded before receiving traffic."""

    assets = container.catalog.list_assets()
    return {"status": "ready", "catalog_assets": len(assets)}
