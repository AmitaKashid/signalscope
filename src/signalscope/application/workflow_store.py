"""In-memory storage for completed workflow results used by the demo dashboard."""

from __future__ import annotations

from threading import Lock

from signalscope.domain.models import DecisionBrief


class WorkflowStore:
    """Retain recent workflow outputs so approvals and dashboard refreshes are stable."""

    def __init__(self, max_records: int = 100) -> None:
        self._max_records = max_records
        self._records: dict[str, DecisionBrief] = {}
        self._order: list[str] = []
        self._lock = Lock()

    def save(self, result: DecisionBrief) -> DecisionBrief:
        """Persist a result and evict the oldest records after the configured capacity."""

        with self._lock:
            if result.workflow_id not in self._records:
                self._order.append(result.workflow_id)
            self._records[result.workflow_id] = result
            while len(self._order) > self._max_records:
                expired = self._order.pop(0)
                self._records.pop(expired, None)
        return result

    def get(self, workflow_id: str) -> DecisionBrief | None:
        """Return one retained decision brief."""

        with self._lock:
            return self._records.get(workflow_id)

    def list_recent(self, limit: int = 20) -> list[DecisionBrief]:
        """Return the newest results first."""

        with self._lock:
            identifiers = list(reversed(self._order[-limit:]))
            return [
                self._records[identifier]
                for identifier in identifiers
                if identifier in self._records
            ]
