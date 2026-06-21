"""Typed Pydantic models for requests, evidence, recommendations, and workflow state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from signalscope.domain.enums import (
    DistributionChannel,
    RecommendationDecision,
    RightsStatus,
    Severity,
    TraceStatus,
    WorkflowStatus,
)


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(timezone.utc)


class TranscriptSegment(BaseModel):
    """A time-bounded transcript segment that can be cited as evidence."""

    model_config = ConfigDict(frozen=True)

    segment_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str = Field(min_length=1)

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


class Asset(BaseModel):
    """A synthetic media catalog item used by the demo and local evaluation harness."""

    model_config = ConfigDict(frozen=True)

    asset_id: str
    title: str
    synopsis: str
    language: str = "en"
    duration_seconds: int = Field(gt=0)
    published_at: datetime
    rights_status: RightsStatus
    rights_note: str
    allowed_channels: list[DistributionChannel]
    content_rating: Literal["general", "teen", "adult"] = "general"
    topics: list[str] = Field(min_length=1)
    audience_tags: list[str] = Field(default_factory=list)
    keyframe_tags: list[str] = Field(default_factory=list)
    visual_summary: str
    transcript: list[TranscriptSegment] = Field(default_factory=list)
    source_url: HttpUrl | None = None

    @field_validator("topics", "audience_tags", "keyframe_tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return sorted({item.strip().lower() for item in values if item.strip()})


class CampaignBrief(BaseModel):
    """Normalized request contract created before tool use begins."""

    request_id: str
    raw_request: str = Field(min_length=8, max_length=4000)
    campaign_goal: str = Field(min_length=3, max_length=300)
    target_audience: str = Field(default="general audience", max_length=120)
    topics: list[str] = Field(default_factory=list)
    requested_channels: list[DistributionChannel] = Field(default_factory=list)
    preferred_language: str | None = None
    maximum_duration_seconds: int | None = Field(default=None, gt=0)
    safety_sensitive: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("topics")
    @classmethod
    def deduplicate_topics(cls, values: list[str]) -> list[str]:
        return sorted({topic.strip().lower() for topic in values if topic.strip()})


class EvidenceReference(BaseModel):
    """Inspectable evidence used to justify a recommendation or a rejection."""

    evidence_id: str
    asset_id: str
    evidence_type: Literal["transcript", "metadata", "policy", "visual"]
    excerpt: str
    source_label: str
    start_seconds: float | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, ge=0)
    retrieval_score: float = Field(ge=0, le=1)
    citation_url: HttpUrl | None = None


class PolicyFinding(BaseModel):
    """A deterministic policy evaluation result."""

    rule_id: str
    severity: Severity
    title: str
    explanation: str
    asset_id: str | None = None
    remediation: str | None = None


class ScoreBreakdown(BaseModel):
    """Factor-level scores retained for transparent recommendation ranking."""

    relevance: float = Field(ge=0, le=1)
    audience_fit: float = Field(ge=0, le=1)
    channel_fit: float = Field(ge=0, le=1)
    rights_confidence: float = Field(ge=0, le=1)
    safety_fit: float = Field(ge=0, le=1)
    freshness: float = Field(ge=0, le=1)
    total: float = Field(ge=0, le=1)

    @classmethod
    def weighted(
        cls,
        *,
        relevance: float,
        audience_fit: float,
        channel_fit: float,
        rights_confidence: float,
        safety_fit: float,
        freshness: float,
    ) -> "ScoreBreakdown":
        total = (
            0.36 * relevance
            + 0.16 * audience_fit
            + 0.16 * channel_fit
            + 0.18 * rights_confidence
            + 0.08 * safety_fit
            + 0.06 * freshness
        )
        return cls(
            relevance=relevance,
            audience_fit=audience_fit,
            channel_fit=channel_fit,
            rights_confidence=rights_confidence,
            safety_fit=safety_fit,
            freshness=freshness,
            total=round(min(max(total, 0.0), 1.0), 4),
        )


class Counterfactual(BaseModel):
    """A concrete change that could change a recommendation outcome."""

    condition: str
    impact: str


class Recommendation(BaseModel):
    """Recommendation, exclusion, or review decision for one media asset."""

    asset: Asset
    decision: RecommendationDecision
    score: ScoreBreakdown
    rank: int | None = Field(default=None, ge=1)
    reasons_selected: list[str] = Field(default_factory=list)
    reasons_excluded: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    policy_findings: list[PolicyFinding] = Field(default_factory=list)
    counterfactuals: list[Counterfactual] = Field(default_factory=list)


class TraceEvent(BaseModel):
    """One node-level audit record for workflow observability."""

    event_id: str
    workflow_id: str
    node: str
    status: TraceStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    attributes: dict[str, str | int | float | bool] = Field(default_factory=dict)
    error: str | None = None


class QualityGateResult(BaseModel):
    """Guardrail output that determines whether the workflow can request approval."""

    status: WorkflowStatus
    evidence_coverage: float = Field(ge=0, le=1)
    unsupported_claim_count: int = Field(ge=0)
    blocker_count: int = Field(ge=0)
    notes: list[str] = Field(default_factory=list)


class DecisionBrief(BaseModel):
    """Client-facing output produced by the governed workflow."""

    workflow_id: str
    status: WorkflowStatus
    brief: CampaignBrief
    executive_summary: str
    recommendations: list[Recommendation]
    excluded_assets: list[Recommendation] = Field(default_factory=list)
    quality_gate: QualityGateResult
    trace: list[TraceEvent]
    created_at: datetime = Field(default_factory=utc_now)


class ApprovalRequest(BaseModel):
    """Human approval input for a previously completed workflow."""

    reviewer: str = Field(min_length=2, max_length=120)
    decision: Literal["approve", "reject", "needs_review"]
    comment: str | None = Field(default=None, max_length=1000)


class ApprovalRecord(BaseModel):
    """Persisted human-in-the-loop decision."""

    workflow_id: str
    reviewer: str
    decision: WorkflowStatus
    comment: str | None
    decided_at: datetime = Field(default_factory=utc_now)


class CampaignRequest(BaseModel):
    """Public API request DTO."""

    request: str = Field(min_length=8, max_length=4000)
    requested_channels: list[DistributionChannel] = Field(default_factory=list)
    maximum_results: Annotated[int, Field(ge=1, le=10)] = 5
