"""Converts unstructured campaign language into an inspectable typed task contract."""

from __future__ import annotations

import re
from uuid import uuid4

from signalscope.domain.enums import DistributionChannel
from signalscope.domain.models import CampaignBrief
from signalscope.infrastructure.text import tokenize

KNOWN_TOPICS = {
    "ai": ("ai", "algorithm", "automated", "explainability", "digital"),
    "climate": ("climate", "heat", "flood", "forest", "energy", "water", "drought"),
    "circular economy": ("circular", "repair", "reuse", "packaging", "waste", "food rescue"),
    "mobility": ("mobility", "bike", "bicycle", "transport", "commuter", "city"),
    "community": ("community", "neighborhood", "volunteer", "family", "culture"),
    "science": ("science", "sensor", "research", "biodiversity"),
}

CHANNEL_HINTS: dict[DistributionChannel, tuple[str, ...]] = {
    DistributionChannel.SOCIAL: ("social", "instagram", "tiktok", "reels", "linkedin"),
    DistributionChannel.MEDIA_LIBRARY: ("media library", "mediathek", "library", "on-demand"),
    DistributionChannel.NEWSLETTER: ("newsletter", "email", "mailing"),
    DistributionChannel.BROADCAST: ("broadcast", "television", "tv", "linear"),
    DistributionChannel.INTERNAL: ("internal", "intranet", "staff"),
}

SENSITIVE_HINTS = ("flood", "trauma", "injury", "death", "violence", "crisis")


class BriefParser:
    """Rule-assisted parser with deterministic extraction and conservative defaults.

    In a production deployment, this component can invoke a structured-output LLM,
    but the final contract must still pass Pydantic validation and policy checks.
    """

    def parse(
        self,
        *,
        raw_request: str,
        explicit_channels: list[DistributionChannel],
        request_id: str | None = None,
    ) -> CampaignBrief:
        """Create a typed brief from user language and explicit request parameters."""

        lower = raw_request.lower()
        channels = explicit_channels or self._extract_channels(lower)
        topics = self._extract_topics(lower)
        audience = self._extract_audience(raw_request)
        max_duration = self._extract_duration(lower)

        return CampaignBrief(
            request_id=request_id or str(uuid4()),
            raw_request=raw_request,
            campaign_goal=self._extract_goal(raw_request),
            target_audience=audience,
            topics=topics,
            requested_channels=channels,
            preferred_language="en" if "english" in lower else None,
            maximum_duration_seconds=max_duration,
            safety_sensitive=any(hint in lower for hint in SENSITIVE_HINTS),
        )

    @staticmethod
    def _extract_goal(raw_request: str) -> str:
        cleaned = " ".join(raw_request.strip().split())
        first_sentence = re.split(r"[.!?]", cleaned, maxsplit=1)[0].strip()
        return first_sentence[:300] if first_sentence else "Identify suitable media assets."

    @staticmethod
    def _extract_channels(lower: str) -> list[DistributionChannel]:
        channels = [
            channel
            for channel, hints in CHANNEL_HINTS.items()
            if any(hint in lower for hint in hints)
        ]
        return channels or [DistributionChannel.MEDIA_LIBRARY]

    @staticmethod
    def _extract_topics(lower: str) -> list[str]:
        topics = [
            canonical
            for canonical, hints in KNOWN_TOPICS.items()
            if any(hint in lower for hint in hints)
        ]
        if topics:
            return topics

        # Preserve meaningful out-of-vocabulary terms to avoid discarding user intent.
        candidates = [token for token in tokenize(lower) if len(token) >= 5]
        return candidates[:4]

    @staticmethod
    def _extract_audience(raw_request: str) -> str:
        age_match = re.search(r"\b(\d{1,2}\s*(?:-|to)\s*\d{1,2})\b", raw_request)
        if age_match:
            return age_match.group(1).replace("to", "-").replace(" ", "")

        for label in ("young adults", "students", "families", "professionals", "general audience"):
            if label in raw_request.lower():
                return label

        return "general audience"

    @staticmethod
    def _extract_duration(lower: str) -> int | None:
        if any(hint in lower for hint in ("short", "reel", "instagram", "tiktok")):
            return 60

        seconds_match = re.search(r"(\d{1,4})\s*(?:seconds|second|sec|s)\b", lower)
        if seconds_match:
            return int(seconds_match.group(1))

        minutes_match = re.search(r"(\d{1,2})\s*(?:minutes|minute|min)\b", lower)
        if minutes_match:
            return int(minutes_match.group(1)) * 60

        return None
