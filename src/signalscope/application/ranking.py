"""Transparent recommendation ranking with deterministic factor contributions."""

from __future__ import annotations

from dataclasses import dataclass

from signalscope.domain.enums import (
    DistributionChannel,
    RecommendationDecision,
    RightsStatus,
    Severity,
)
from signalscope.domain.models import CampaignBrief, PolicyFinding, Recommendation, ScoreBreakdown
from signalscope.infrastructure.hybrid_retriever import RetrievedAsset, freshness_score
from signalscope.infrastructure.text import token_overlap


@dataclass(frozen=True)
class RankedCandidate:
    """Intermediate candidate retaining factor scores before explanation generation."""

    recommendation: Recommendation
    retrieval_score: float


class RecommendationRanker:
    """Combine retrieval quality with editorial feasibility and rights confidence."""

    def rank(
        self,
        *,
        brief: CampaignBrief,
        candidates: list[RetrievedAsset],
        policy_findings_by_asset: dict[str, list[PolicyFinding]],
    ) -> list[RankedCandidate]:
        """Produce recommendation or exclusion decisions without hiding hard constraints."""

        ranked: list[RankedCandidate] = []
        requested_channels = {channel.value for channel in brief.requested_channels}

        for retrieved_candidate in candidates:
            asset = retrieved_candidate.asset
            findings = policy_findings_by_asset.get(asset.asset_id, [])
            blockers = [finding for finding in findings if finding.severity is Severity.BLOCKER]

            audience_fit = self._audience_fit(asset.audience_tags, brief.target_audience)
            channel_fit = self._channel_fit(asset.allowed_channels, requested_channels)
            rights_confidence = self._rights_score(asset.rights_status)
            safety_fit = 0.0 if blockers else self._safety_fit(findings)
            relevance = min(retrieved_candidate.final_score * 1.25, 1.0)
            fresh = freshness_score(asset.published_at)

            score = ScoreBreakdown.weighted(
                relevance=relevance,
                audience_fit=audience_fit,
                channel_fit=channel_fit,
                rights_confidence=rights_confidence,
                safety_fit=safety_fit,
                freshness=fresh,
            )

            decision = (
                RecommendationDecision.EXCLUDE if blockers else RecommendationDecision.RECOMMEND
            )
            recommendation = Recommendation(
                asset=asset,
                decision=decision,
                score=score,
                reasons_selected=[],
                reasons_excluded=[],
                evidence=retrieved_candidate.evidence,
                policy_findings=findings,
                counterfactuals=[],
            )
            ranked.append(
                RankedCandidate(
                    recommendation=recommendation, retrieval_score=retrieved_candidate.final_score
                )
            )

        eligible = sorted(
            [
                ranked_item
                for ranked_item in ranked
                if ranked_item.recommendation.decision is RecommendationDecision.RECOMMEND
            ],
            key=lambda ranked_item: ranked_item.recommendation.score.total,
            reverse=True,
        )
        excluded = sorted(
            [
                ranked_item
                for ranked_item in ranked
                if ranked_item.recommendation.decision is RecommendationDecision.EXCLUDE
            ],
            key=lambda ranked_item: ranked_item.recommendation.score.total,
            reverse=True,
        )

        for position, ranked_item in enumerate(eligible, start=1):
            ranked_item.recommendation.rank = position
        return [*eligible, *excluded]

    @staticmethod
    def _audience_fit(asset_tags: list[str], target_audience: str) -> float:
        target_tokens = target_audience.lower().replace("-", " ").split()
        asset_tokens = " ".join(asset_tags).lower().replace("-", " ").split()
        direct = token_overlap(target_tokens, asset_tokens)

        normalized_target = target_audience.lower().replace(" ", "")
        mapped = {
            "1834": {"18-34", "16-24"},
            "2534": {"25-44", "18-34"},
            "youngadults": {"18-34", "16-24"},
            "students": {"students", "16-24", "18-34"},
            "families": {"families", "general"},
            "generalaudience": {"general"},
        }
        indirect = 0.0
        for pattern, supported_tags in mapped.items():
            if pattern in normalized_target and any(tag in asset_tags for tag in supported_tags):
                indirect = 0.9
        return round(max(direct, indirect, 0.35 if "general" in asset_tags else 0.0), 4)

    @staticmethod
    def _channel_fit(
        asset_channels: list[DistributionChannel], requested_channels: set[str]
    ) -> float:
        if not requested_channels:
            return 0.8
        actual = {channel.value for channel in asset_channels}
        return round(len(actual & requested_channels) / len(requested_channels), 4)

    @staticmethod
    def _rights_score(status: RightsStatus) -> float:
        return {
            RightsStatus.CLEARED: 1.0,
            RightsStatus.RESTRICTED: 0.45,
            RightsStatus.UNKNOWN: 0.1,
        }[status]

    @staticmethod
    def _safety_fit(findings: list[PolicyFinding]) -> float:
        return 0.7 if any(finding.severity is Severity.WARNING for finding in findings) else 1.0
