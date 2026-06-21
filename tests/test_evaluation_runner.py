from signalscope.evaluation.runner import EvaluationRunner


def test_evaluation_runner_returns_aggregate_metrics(monkeypatch) -> None:
    monkeypatch.setenv("SIGNALSCOPE_ENVIRONMENT", "test")
    runner = EvaluationRunner()
    report = runner.run()

    assert report["task_count"] >= 5
    assert "mean_recall_at_3" in report["metrics"]
    assert report["metrics"]["disallowed_recommendation_count"] == 0
