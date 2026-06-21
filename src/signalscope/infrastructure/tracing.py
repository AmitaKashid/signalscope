"""Workflow trace capture with an in-memory exporter for local demos and tests."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from time import perf_counter
from typing import Iterator
from uuid import uuid4

from signalscope.domain.enums import TraceStatus
from signalscope.domain.models import TraceEvent


class TraceRecorder:
    """Accumulate node-level audit events for a single workflow execution."""

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        self._events: list[TraceEvent] = []

    @contextmanager
    def span(self, node: str, **attributes: str | int | float | bool) -> Iterator[None]:
        """Record completion duration and error state for a workflow node."""

        event = TraceEvent(
            event_id=str(uuid4()),
            workflow_id=self.workflow_id,
            node=node,
            status=TraceStatus.STARTED,
            started_at=datetime.now(timezone.utc),
            attributes=dict(attributes),
        )
        self._events.append(event)
        started = perf_counter()
        try:
            yield
        except Exception as error:
            event.status = TraceStatus.FAILED
            event.error = str(error)
            event.completed_at = datetime.now(timezone.utc)
            event.duration_ms = round((perf_counter() - started) * 1000, 2)
            raise
        else:
            event.status = TraceStatus.COMPLETED
            event.completed_at = datetime.now(timezone.utc)
            event.duration_ms = round((perf_counter() - started) * 1000, 2)

    def snapshot(self) -> list[TraceEvent]:
        """Return a safe copy of captured trace events."""

        return list(self._events)
