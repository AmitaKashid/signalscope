"""File-backed media catalog repository for demo, tests, and offline portfolio reviews."""

from __future__ import annotations

import json
from pathlib import Path

from signalscope.domain.models import Asset


class CatalogRepository:
    """Loads immutable demo assets from JSON and exposes explicit query methods."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._assets: dict[str, Asset] = {}
        self._loaded = False

    def load(self) -> None:
        """Load catalog data exactly once to provide deterministic request behavior."""

        if self._loaded:
            return

        asset_path = self._data_dir / "assets.json"
        payload = json.loads(asset_path.read_text(encoding="utf-8"))
        self._assets = {asset["asset_id"]: Asset.model_validate(asset) for asset in payload}
        self._loaded = True

    def list_assets(self) -> list[Asset]:
        """Return all catalog assets sorted by identifier for stable tests."""

        self.load()
        return [self._assets[key] for key in sorted(self._assets)]

    def get_asset(self, asset_id: str) -> Asset | None:
        """Return an asset if it is present in the catalog."""

        self.load()
        return self._assets.get(asset_id)

    def require_asset(self, asset_id: str) -> Asset:
        """Return a requested asset or raise a descriptive lookup error."""

        asset = self.get_asset(asset_id)
        if asset is None:
            raise KeyError(f"Unknown asset_id={asset_id}")
        return asset
