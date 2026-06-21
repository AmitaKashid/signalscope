"""MCP server exposing deterministic editorial policy checks."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from signalscope.application.brief_parser import BriefParser
from signalscope.core.config import get_settings
from signalscope.domain.enums import DistributionChannel
from signalscope.infrastructure.catalog_repository import CatalogRepository
from signalscope.infrastructure.policy_engine import PolicyEngine

mcp = FastMCP("SignalScope Editorial Policy")


@lru_cache(maxsize=1)
def _services() -> tuple[CatalogRepository, PolicyEngine, BriefParser]:
    settings = get_settings()
    catalog = CatalogRepository(settings.data_dir)
    catalog.load()
    return catalog, PolicyEngine(settings.data_dir), BriefParser()


@mcp.tool()
def validate_distribution(asset_id: str, channels: list[str]) -> dict[str, Any]:
    """Validate rights, duration, rating, and authorization for requested channels."""

    catalog, policy_engine, brief_parser = _services()
    requested_channels = [DistributionChannel(channel) for channel in channels]
    brief = brief_parser.parse(
        raw_request=f"Validate editorial distribution for {', '.join(channels)}.",
        explicit_channels=requested_channels,
    )
    asset = catalog.require_asset(asset_id)
    findings = policy_engine.evaluate_asset(asset, brief)
    return {
        "asset_id": asset_id,
        "policy_version": policy_engine.version,
        "eligible": not policy_engine.has_blocker(findings),
        "findings": [finding.model_dump(mode="json") for finding in findings],
    }


@mcp.tool()
def check_request_safety(request: str) -> dict[str, Any]:
    """Identify common prompt-injection phrases before tool execution."""

    _, policy_engine, _ = _services()
    findings = policy_engine.validate_request(request)
    return {
        "safe_to_continue": not policy_engine.has_blocker(findings),
        "findings": [finding.model_dump(mode="json") for finding in findings],
    }


@mcp.tool()
def get_editorial_guidance(channel: str) -> dict[str, Any]:
    """Return controlled distribution guidance for a named channel."""

    guidance = {
        "social": {
            "purpose": "Short-form external discovery and engagement.",
            "requirements": [
                "cleared rights",
                "duration at or below 60 seconds",
                "audience-appropriate rating",
            ],
        },
        "newsletter": {
            "purpose": "Editorial context and traffic-driving recommendations.",
            "requirements": [
                "cleared rights",
                "evidence-supported description",
                "human editorial approval",
            ],
        },
        "media_library": {
            "purpose": "Long-form owned-media availability.",
            "requirements": ["cleared rights", "metadata completeness", "human editorial approval"],
        },
        "broadcast": {
            "purpose": "Linear programming or broadcast-adjacent distribution.",
            "requirements": ["cleared rights", "schedule review", "editorial approval"],
        },
        "internal": {
            "purpose": "Internal review and non-public collaboration.",
            "requirements": [
                "access-controlled audience",
                "rights note visible",
                "reviewer accountability",
            ],
        },
    }
    if channel not in guidance:
        raise ValueError(f"Unknown channel '{channel}'.")
    return {"channel": channel, **guidance[channel]}


def main() -> None:
    """Start the stdio MCP server."""

    mcp.run()


if __name__ == "__main__":
    main()
