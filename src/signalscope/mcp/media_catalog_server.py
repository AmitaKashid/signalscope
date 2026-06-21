"""MCP server exposing read-only media catalog retrieval tools."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from signalscope.core.config import get_settings
from signalscope.infrastructure.catalog_repository import CatalogRepository
from signalscope.infrastructure.text import tokenize

mcp = FastMCP("SignalScope Media Catalog")


@lru_cache(maxsize=1)
def _catalog() -> CatalogRepository:
    settings = get_settings()
    repository = CatalogRepository(settings.data_dir)
    repository.load()
    return repository


@mcp.tool()
def search_assets(
    query: str,
    channel: str | None = None,
    topic: str | None = None,
    maximum_results: int = 5,
) -> list[dict[str, Any]]:
    """Search synthetic media metadata and transcripts without modifying catalog state.

    Args:
        query: Editorial requirement or search terms.
        channel: Optional requested distribution channel.
        topic: Optional exact topic filter.
        maximum_results: Number of assets to return, between 1 and 10.
    """

    query_terms = set(tokenize(query))
    rows: list[tuple[float, dict[str, Any]]] = []
    for asset in _catalog().list_assets():
        searchable = " ".join(
            [
                asset.title,
                asset.synopsis,
                asset.visual_summary,
                " ".join(asset.topics),
                " ".join(segment.text for segment in asset.transcript),
            ]
        )
        score = len(query_terms & set(tokenize(searchable))) / max(len(query_terms), 1)
        if channel and channel not in {item.value for item in asset.allowed_channels}:
            continue
        if topic and topic.lower() not in asset.topics:
            continue
        rows.append(
            (
                score,
                {
                    "asset_id": asset.asset_id,
                    "title": asset.title,
                    "synopsis": asset.synopsis,
                    "topics": asset.topics,
                    "duration_seconds": asset.duration_seconds,
                    "rights_status": asset.rights_status.value,
                    "allowed_channels": [item.value for item in asset.allowed_channels],
                    "score": round(score, 4),
                },
            )
        )

    return [
        row
        for _, row in sorted(rows, key=lambda item: item[0], reverse=True)[
            : max(1, min(maximum_results, 10))
        ]
    ]


@mcp.tool()
def get_asset_metadata(asset_id: str) -> dict[str, Any]:
    """Return catalog metadata and rights notes for a specific asset."""

    asset = _catalog().require_asset(asset_id)
    return {
        "asset_id": asset.asset_id,
        "title": asset.title,
        "topics": asset.topics,
        "audience_tags": asset.audience_tags,
        "duration_seconds": asset.duration_seconds,
        "rights_status": asset.rights_status.value,
        "rights_note": asset.rights_note,
        "allowed_channels": [item.value for item in asset.allowed_channels],
        "content_rating": asset.content_rating,
        "visual_summary": asset.visual_summary,
    }


@mcp.tool()
def get_transcript_segment(
    asset_id: str, start_seconds: float = 0, end_seconds: float = 99999
) -> list[dict[str, Any]]:
    """Return citeable transcript segments that overlap the supplied time window."""

    asset = _catalog().require_asset(asset_id)
    return [
        {
            "segment_id": segment.segment_id,
            "start_seconds": segment.start_seconds,
            "end_seconds": segment.end_seconds,
            "text": segment.text,
        }
        for segment in asset.transcript
        if segment.end_seconds >= start_seconds and segment.start_seconds <= end_seconds
    ]


def main() -> None:
    """Start the stdio MCP server."""

    mcp.run()


if __name__ == "__main__":
    main()
