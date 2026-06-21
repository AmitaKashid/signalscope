"""Typed state passed between governed workflow nodes."""

from __future__ import annotations

from typing import Any, TypedDict

from signalscope.application.ranking import RankedCandidate
from signalscope.domain.enums import DistributionChannel
from signalscope.domain.models import (
    CampaignBrief,
    DecisionBrief,
    PolicyFinding,
    QualityGateResult,
    Recommendation,
)
from signalscope.infrastructure.hybrid_retriever import RetrievedAsset
from signalscope.infrastructure.tracing import TraceRecorder


class MediaWorkflowState(TypedDict, total=False):
    """All state is explicit so each node has a clear contract and audit boundary."""

    workflow_id: str
    raw_request: str
    explicit_channels: list[DistributionChannel]
    maximum_results: int
    trace_recorder: TraceRecorder

    request_findings: list[PolicyFinding]
    blocked: bool
    brief: CampaignBrief
    candidates: list[RetrievedAsset]
    policy_findings_by_asset: dict[str, list[PolicyFinding]]
    ranked_candidates: list[RankedCandidate]
    recommendations: list[Recommendation]
    quality_gate: QualityGateResult
    decision_brief: DecisionBrief
    diagnostics: dict[str, Any]
