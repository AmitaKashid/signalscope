"""Thread-safe in-memory approval storage for local demos.

Replace with a repository backed by Cloud SQL or PostgreSQL in a multi-user deployment.
"""

from __future__ import annotations

from threading import Lock

from signalscope.domain.enums import WorkflowStatus
from signalscope.domain.models import ApprovalRecord, ApprovalRequest


class ApprovalStore:
    """Persist human decisions separately from agent outputs."""

    def __init__(self) -> None:
        self._records: dict[str, ApprovalRecord] = {}
        self._lock = Lock()

    def record(self, workflow_id: str, request: ApprovalRequest) -> ApprovalRecord:
        """Create or replace a decision for a workflow."""

        decision_mapping = {
            "approve": WorkflowStatus.APPROVED,
            "reject": WorkflowStatus.REJECTED,
            "needs_review": WorkflowStatus.NEEDS_REVIEW,
        }
        record = ApprovalRecord(
            workflow_id=workflow_id,
            reviewer=request.reviewer,
            decision=decision_mapping[request.decision],
            comment=request.comment,
        )
        with self._lock:
            self._records[workflow_id] = record
        return record

    def get(self, workflow_id: str) -> ApprovalRecord | None:
        """Return the latest recorded human decision."""

        with self._lock:
            return self._records.get(workflow_id)
