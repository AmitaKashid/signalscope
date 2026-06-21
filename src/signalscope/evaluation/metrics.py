"""Pure metric functions kept independent from workflow implementation."""

from __future__ import annotations

from collections.abc import Iterable


def recall_at_k(retrieved: Iterable[str], expected: Iterable[str], k: int) -> float:
    """Measure expected relevant items recovered among the top k positions."""

    expected_set = set(expected)
    if not expected_set:
        return 1.0
    retrieved_set = set(list(retrieved)[:k])
    return len(retrieved_set & expected_set) / len(expected_set)


def precision_at_k(retrieved: Iterable[str], expected: Iterable[str], k: int) -> float:
    """Measure top-k proportion that is relevant for tasks with known positives."""

    expected_set = set(expected)
    result = list(retrieved)[:k]
    if not result:
        return 0.0
    return len(set(result) & expected_set) / len(result)


def mean(values: Iterable[float]) -> float:
    """Return a stable average for an iterable of floats."""

    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0
