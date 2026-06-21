"""Small deterministic text utilities used by the local demo retrieval backend."""

from __future__ import annotations

import re
from collections.abc import Iterable

TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,}")
STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "for",
    "from",
    "into",
    "must",
    "that",
    "the",
    "this",
    "with",
    "will",
    "your",
    "you",
    "video",
    "find",
    "recommend",
    "need",
    "want",
    "please",
}


def tokenize(text: str) -> list[str]:
    """Normalize text into meaningful lowercase tokens."""

    return [token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS]


def token_overlap(left: Iterable[str], right: Iterable[str]) -> float:
    """Compute Jaccard overlap for normalized tag lists."""

    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    """Return whether any case-insensitive phrase occurs in text."""

    normalized = text.lower()
    return any(phrase.lower() in normalized for phrase in phrases)
