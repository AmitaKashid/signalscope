"""Enumerations used by the media intelligence domain."""

from __future__ import annotations

from enum import Enum


class DistributionChannel(str, Enum):
    SOCIAL = "social"
    MEDIA_LIBRARY = "media_library"
    NEWSLETTER = "newsletter"
    BROADCAST = "broadcast"
    INTERNAL = "internal"


class RightsStatus(str, Enum):
    CLEARED = "cleared"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class WorkflowStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class TraceStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RecommendationDecision(str, Enum):
    RECOMMEND = "recommend"
    EXCLUDE = "exclude"
    REVIEW = "review"
