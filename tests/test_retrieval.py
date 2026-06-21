from signalscope.application.brief_parser import BriefParser
from signalscope.domain.enums import DistributionChannel


def test_hybrid_retrieval_surfaces_relevant_climate_assets(container) -> None:
    brief = BriefParser().parse(
        raw_request="Find a short rights-cleared climate story for young adults on social media.",
        explicit_channels=[DistributionChannel.SOCIAL],
    )

    results = container.workflow._retriever.search(brief, limit=5)
    asset_ids = [result.asset.asset_id for result in results]

    assert "asset-forest-sensors" in asset_ids
    assert any(result.evidence for result in results)
    assert all(0 <= result.final_score <= 1 for result in results)
