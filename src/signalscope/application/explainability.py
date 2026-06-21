"""Generate factor-level explanations and actionable counterfactuals."""

from __future__ import annotations

from signalscope.domain.enums import RecommendationDecision, RightsStatus, Severity
from signalscope.domain.models import CampaignBrief, Counterfactual, Recommendation


class ExplanationService:
    """Build explanations from deterministic scores, evidence, and policy findings."""

    def enrich(self, brief: CampaignBrief, recommendation: Recommendation) -> Recommendation:
        """Mutate a typed recommendation only by adding inspectable derived rationale."""

        asset = recommendation.asset
        score = recommendation.score
        if recommendation.decision is RecommendationDecision.RECOMMEND:
            recommendation.reasons_selected.extend(
                [
                    f"Content relevance scored {score.relevance:.0%} against the normalized campaign brief.",
                    f"Audience fit scored {score.audience_fit:.0%} for '{brief.target_audience}'.",
                    f"Channel eligibility scored {score.channel_fit:.0%} across the requested distribution channels.",
                ]
            )
            if asset.rights_status is RightsStatus.CLEARED:
                recommendation.reasons_selected.append(
                    "Rights status is cleared for the requested distribution pathway."
                )
            if score.freshness >= 0.8:
                recommendation.reasons_selected.append(
                    "The asset is recent enough to support a timely editorial angle."
                )
        else:
            blockers = [
                finding
                for finding in recommendation.policy_findings
                if finding.severity is Severity.BLOCKER
            ]
            recommendation.reasons_excluded.extend(
                [finding.explanation for finding in blockers]
                or ["The asset failed a deterministic editorial or distribution constraint."]
            )

        recommendation.counterfactuals.extend(self._counterfactuals(brief, recommendation))
        return recommendation

    @staticmethod
    def _counterfactuals(
        brief: CampaignBrief, recommendation: Recommendation
    ) -> list[Counterfactual]:
        asset = recommendation.asset
        counterfactuals: list[Counterfactual] = []

        if asset.rights_status is not RightsStatus.CLEARED and brief.requested_channels:
            requested = ", ".join(
                channel.value.replace("_", " ") for channel in brief.requested_channels
            )
            counterfactuals.append(
                Counterfactual(
                    condition=f"Rights clearance is recorded for {requested}.",
                    impact="The asset can be reconsidered for external distribution ranking.",
                )
            )

        if (
            brief.maximum_duration_seconds
            and asset.duration_seconds > brief.maximum_duration_seconds
        ):
            counterfactuals.append(
                Counterfactual(
                    condition=(
                        f"A version under {brief.maximum_duration_seconds}s is produced "
                        f"from the current {asset.duration_seconds}s asset."
                    ),
                    impact="The duration warning would be removed for the requested channel.",
                )
            )

        if recommendation.score.audience_fit < 0.5:
            counterfactuals.append(
                Counterfactual(
                    condition="The campaign audience is broadened or a targeted edit is produced.",
                    impact="Audience-fit weighting may improve enough to change relative ranking.",
                )
            )

        if not counterfactuals:
            counterfactuals.append(
                Counterfactual(
                    condition="No material policy or format condition changes.",
                    impact="The current recommendation remains suitable under the present brief.",
                )
            )
        return counterfactuals
