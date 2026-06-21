"""Versioned evaluation runner for SignalScope's governed workflow."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from signalscope.api.container import build_container
from signalscope.core.config import get_settings
from signalscope.domain.enums import DistributionChannel, RecommendationDecision
from signalscope.domain.models import CampaignRequest
from signalscope.evaluation.metrics import mean, precision_at_k, recall_at_k


@dataclass(frozen=True)
class EvaluationCaseResult:
    """One task result with traceable outcome measures."""

    task_id: str
    top_asset_ids: list[str]
    expected_asset_ids: list[str]
    disallowed_asset_ids: list[str]
    recall_at_3: float
    precision_at_3: float
    disallowed_recommendation_count: int
    evidence_coverage: float
    valid_trace_rate: float
    workflow_status: str
    latency_ms: float


class EvaluationRunner:
    """Execute a fixed golden set and serialize an inspectable JSON report."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.container = build_container(self.settings)
        self.container.catalog.load()

    def run(self, tasks_path: Path | None = None) -> dict[str, Any]:
        """Run golden tasks and aggregate retrieval, guardrail, trace, and latency metrics."""

        path = tasks_path or self.settings.data_dir / "evaluation_tasks.json"
        tasks = json.loads(path.read_text(encoding="utf-8"))
        results = [self._run_case(task) for task in tasks]

        report = {
            "report_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset": str(path),
            "task_count": len(results),
            "metrics": {
                "mean_recall_at_3": round(mean(result.recall_at_3 for result in results), 4),
                "mean_precision_at_3": round(mean(result.precision_at_3 for result in results), 4),
                "mean_evidence_coverage": round(
                    mean(result.evidence_coverage for result in results), 4
                ),
                "mean_valid_trace_rate": round(
                    mean(result.valid_trace_rate for result in results), 4
                ),
                "mean_latency_ms": round(mean(result.latency_ms for result in results), 2),
                "disallowed_recommendation_count": sum(
                    result.disallowed_recommendation_count for result in results
                ),
            },
            "cases": [asdict(result) for result in results],
        }
        return report

    def _run_case(self, task: dict[str, Any]) -> EvaluationCaseResult:
        started = perf_counter()
        request = CampaignRequest(
            request=task["request"],
            requested_channels=[
                DistributionChannel(channel) for channel in task.get("channels", [])
            ],
            maximum_results=3,
        )
        result = self.container.workflow.run(request)
        latency_ms = (perf_counter() - started) * 1000

        top_assets = [
            recommendation.asset.asset_id
            for recommendation in result.recommendations
            if recommendation.decision is RecommendationDecision.RECOMMEND
        ]
        expected = task.get("expected_asset_ids", [])
        disallowed = task.get("disallowed_asset_ids", [])
        disallowed_count = len(set(top_assets) & set(disallowed))
        trace_completed = sum(event.status.value == "completed" for event in result.trace)
        valid_trace_rate = trace_completed / max(len(result.trace), 1)

        return EvaluationCaseResult(
            task_id=task["task_id"],
            top_asset_ids=top_assets,
            expected_asset_ids=expected,
            disallowed_asset_ids=disallowed,
            recall_at_3=round(recall_at_k(top_assets, expected, 3), 4),
            precision_at_3=round(precision_at_k(top_assets, expected, 3), 4),
            disallowed_recommendation_count=disallowed_count,
            evidence_coverage=result.quality_gate.evidence_coverage,
            valid_trace_rate=round(valid_trace_rate, 4),
            workflow_status=result.status.value,
            latency_ms=round(latency_ms, 2),
        )


def main() -> None:
    """Run evaluation and write a timestamped report file."""

    parser = argparse.ArgumentParser(description="Evaluate the SignalScope workflow.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/evaluations"),
        help="Directory for generated JSON reports.",
    )
    parser.add_argument(
        "--tasks",
        type=Path,
        default=None,
        help="Optional path to an alternate task set.",
    )
    args = parser.parse_args()

    report = EvaluationRunner().run(args.tasks)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = (
        args.output_dir / f"evaluation-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(path), "metrics": report["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
