"""Quality gate that blocks unsupported or policy-unsafe outputs before approval."""

from __future__ import annotations

from signalscope.domain.enums import RecommendationDecision, Severity, WorkflowStatus
from signalscope.domain.models import QualityGateResult, Recommendation


class QualityGate:
    """Check evidence completeness and policy blockers using deterministic thresholds."""

    def __init__(self, minimum_evidence_coverage: float) -> None:
        self._minimum_evidence_coverage = minimum_evidence_coverage

    def evaluate(self, recommendations: list[Recommendation]) -> QualityGateResult:
        """Return approval status and explicit reviewer notes."""

        proposed = [
            recommendation
            for recommendation in recommendations
            if recommendation.decision is RecommendationDecision.RECOMMEND
        ]
        proposed_with_evidence = [
            recommendation for recommendation in proposed if recommendation.evidence
        ]
        evidence_coverage = len(proposed_with_evidence) / max(len(proposed), 1)

        blocker_count = sum(
            1
            for recommendation in recommendations
            for finding in recommendation.policy_findings
            if finding.severity is Severity.BLOCKER
        )
        unsupported_claim_count = sum(
            1
            for recommendation in proposed
            if not recommendation.reasons_selected or not recommendation.evidence
        )

        notes: list[str] = []
        status = WorkflowStatus.PENDING_APPROVAL
        if not proposed:
            status = WorkflowStatus.BLOCKED
            notes.append("No publishable assets remain after deterministic policy checks.")
        elif evidence_coverage < self._minimum_evidence_coverage:
            status = WorkflowStatus.NEEDS_REVIEW
            notes.append(
                f"Evidence coverage {evidence_coverage:.0%} is below the configured "
                f"{self._minimum_evidence_coverage:.0%} threshold."
            )
        elif unsupported_claim_count:
            status = WorkflowStatus.NEEDS_REVIEW
            notes.append("At least one candidate lacks an explanation or supporting evidence.")
        else:
            notes.append("All proposed recommendations include evidence and await human approval.")

        if blocker_count:
            notes.append(f"{blocker_count} policy blocker(s) were recorded on excluded candidates.")

        return QualityGateResult(
            status=status,
            evidence_coverage=round(evidence_coverage, 4),
            unsupported_claim_count=unsupported_claim_count,
            blocker_count=blocker_count,
            notes=notes,
        )
