"""Narrative-generation boundary with deterministic and optional OpenAI implementations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, cast

from signalscope.core.config import Settings
from signalscope.domain.models import CampaignBrief, Recommendation


class NarrativeClient(Protocol):
    """Small provider boundary used only after deterministic evidence and policy evaluation."""

    def summarize(self, brief: CampaignBrief, recommendations: Sequence[Recommendation]) -> str:
        """Create a concise human-readable decision summary."""


class DeterministicNarrativeClient:
    """Safe local narrative formatter used for offline demos and repeatable evaluations."""

    def summarize(self, brief: CampaignBrief, recommendations: Sequence[Recommendation]) -> str:
        selected = [
            recommendation for recommendation in recommendations if recommendation.rank is not None
        ]
        if not selected:
            return (
                "No asset can be recommended because the request did not pass the configured "
                "rights, channel, and evidence safeguards."
            )

        top = selected[0]
        channels = ", ".join(
            channel.value.replace("_", " ") for channel in brief.requested_channels
        )
        runner_up = (
            f" A secondary option is '{selected[1].asset.title}'." if len(selected) > 1 else ""
        )
        return (
            f"SignalScope identified {len(selected)} policy-eligible asset(s) for {channels or 'the requested use case'}. "
            f"'{top.asset.title}' ranks first with {top.score.total:.0%} transparent fit, supported by "
            f"{len(top.evidence)} evidence item(s) and cleared distribution metadata.{runner_up} "
            "All recommendations remain subject to human editorial approval."
        )


class OpenAINarrativeClient:
    """Optional provider adapter that only receives evidence-backed structured context."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def summarize(self, brief: CampaignBrief, recommendations: Sequence[Recommendation]) -> str:
        """Generate an executive summary, falling back should be handled by the factory caller."""

        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except ImportError as error:  # pragma: no cover - only exercised with optional extras
            raise RuntimeError(
                "Install the 'providers' extra to use OpenAI narrative generation."
            ) from error

        client = OpenAI(api_key=self._api_key)
        selected = [
            {
                "title": recommendation.asset.title,
                "score": recommendation.score.total,
                "reasons": recommendation.reasons_selected,
                "evidence": [evidence.excerpt for evidence in recommendation.evidence[:2]],
            }
            for recommendation in recommendations
            if recommendation.rank is not None
        ]
        prompt = (
            "Write a concise editorial recommendation summary. Do not introduce facts not present in the "
            "provided structured evidence. Mention that human approval is required. "
            f"Brief: {brief.model_dump_json()}. Eligible assets: {selected}."
        )
        response = client.responses.create(
            model=self._model,
            input=prompt,
            temperature=0,
        )
        return str(cast(Any, response).output_text).strip()


def build_narrative_client(settings: Settings) -> NarrativeClient:
    """Choose a safe default and avoid runtime dependency on external credentials."""

    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAINarrativeClient(settings.openai_api_key, settings.openai_model)
    return DeterministicNarrativeClient()
