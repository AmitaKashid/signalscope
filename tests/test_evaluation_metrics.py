from signalscope.evaluation.metrics import precision_at_k, recall_at_k


def test_recall_at_k() -> None:
    assert recall_at_k(["a", "b", "c"], ["a", "d"], 3) == 0.5
    assert recall_at_k([], [], 3) == 1.0


def test_precision_at_k() -> None:
    assert precision_at_k(["a", "b", "c"], ["a", "d"], 3) == 1 / 3
    assert precision_at_k([], ["a"], 3) == 0.0
