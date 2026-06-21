"""Catalog inspection endpoints used by the dashboard and MCP examples."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from signalscope.api.container import ApplicationContainer
from signalscope.api.dependencies import get_container
from signalscope.domain.enums import DistributionChannel, RightsStatus
from signalscope.domain.models import Asset

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("", response_model=list[Asset])
def list_assets(
    topic: str | None = Query(default=None),
    rights_status: RightsStatus | None = Query(default=None),
    channel: DistributionChannel | None = Query(default=None),
    container: ApplicationContainer = Depends(get_container),
) -> list[Asset]:
    """Return catalog assets after deterministic metadata filters."""

    assets = container.catalog.list_assets()
    if topic:
        assets = [asset for asset in assets if topic.lower() in asset.topics]
    if rights_status:
        assets = [asset for asset in assets if asset.rights_status is rights_status]
    if channel:
        assets = [asset for asset in assets if channel in asset.allowed_channels]
    return assets


@router.get("/{asset_id}", response_model=Asset)
def get_asset(asset_id: str, container: ApplicationContainer = Depends(get_container)) -> Asset:
    """Fetch one asset, including citeable transcript segments."""

    asset = container.catalog.get_asset(asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' was not found.",
        )
    return asset
