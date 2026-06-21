"""Deterministic rights, channel, content, and request-security checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

from signalscope.domain.enums import RightsStatus, Severity
from signalscope.domain.models import Asset, CampaignBrief, PolicyFinding
from signalscope.infrastructure.text import contains_any


class ChannelPolicy(TypedDict):
    """Validated channel constraints loaded from the versioned policy fixture."""

    max_duration_seconds: int
    requires_rights: str
    allowed_ratings: list[str]


class PolicyPayload(TypedDict):
    """Schema for the local policy fixture."""

    version: str
    channels: dict[str, ChannelPolicy]
    sensitive_topic_keywords: list[str]
    injection_patterns: list[str]


class PolicyEngine:
    """Evaluate explicit editorial policies without delegating compliance decisions to an LLM."""

    def __init__(self, data_dir: Path) -> None:
        raw_payload = json.loads((data_dir / "policies.json").read_text(encoding="utf-8"))
        payload = cast(PolicyPayload, raw_payload)
        self.version = payload["version"]
        self._channels = payload["channels"]
        self._sensitive_topic_keywords = payload["sensitive_topic_keywords"]
        self._injection_patterns = payload["injection_patterns"]

    def validate_request(self, raw_request: str) -> list[PolicyFinding]:
        """Detect common prompt-injection attempts before any tools are used."""

        if not contains_any(raw_request, self._injection_patterns):
            return []
        return [
            PolicyFinding(
                rule_id="SEC-001",
                severity=Severity.BLOCKER,
                title="Potential instruction-injection pattern detected",
                explanation=(
                    "The submitted request contains a phrase associated with attempts to override "
                    "workflow instructions or evidence requirements."
                ),
                remediation="Remove the instruction-like text and resubmit the editorial request.",
            )
        ]

    def evaluate_asset(self, asset: Asset, brief: CampaignBrief) -> list[PolicyFinding]:
        """Return all deterministic findings for one asset against a normalized brief."""

        findings: list[PolicyFinding] = []

        for channel in brief.requested_channels:
            policy = self._channels[channel.value]
            findings.extend(self._channel_findings(asset, channel.value, policy))

        combined_text = " ".join([asset.title, asset.synopsis, *asset.topics]).lower()
        if (
            contains_any(combined_text, self._sensitive_topic_keywords)
            and not brief.safety_sensitive
        ):
            findings.append(
                PolicyFinding(
                    rule_id="ED-004",
                    severity=Severity.WARNING,
                    title="Sensitive topic advisory",
                    explanation=(
                        "The asset includes a potentially sensitive theme. It may require an editorial "
                        "content note or a different campaign framing."
                    ),
                    asset_id=asset.asset_id,
                    remediation="Add an audience-appropriate content advisory before approval.",
                )
            )

        return findings

    @staticmethod
    def has_blocker(findings: list[PolicyFinding]) -> bool:
        """Return whether any finding prevents external recommendation."""

        return any(finding.severity is Severity.BLOCKER for finding in findings)

    def _channel_findings(
        self, asset: Asset, channel: str, policy: ChannelPolicy
    ) -> list[PolicyFinding]:
        findings: list[PolicyFinding] = []
        max_duration = policy["max_duration_seconds"]
        required_rights = RightsStatus(policy["requires_rights"])
        allowed_ratings = set(policy["allowed_ratings"])

        if channel not in {allowed.value for allowed in asset.allowed_channels}:
            findings.append(
                PolicyFinding(
                    rule_id="RIGHTS-001",
                    severity=Severity.BLOCKER,
                    title="Channel not authorized",
                    explanation=f"{asset.title} is not cleared for the requested {channel} channel.",
                    asset_id=asset.asset_id,
                    remediation="Select an authorized channel or request a rights review.",
                )
            )

        required_rank = self._rights_rank(required_rights)
        actual_rank = self._rights_rank(asset.rights_status)
        if actual_rank < required_rank:
            findings.append(
                PolicyFinding(
                    rule_id="RIGHTS-002",
                    severity=Severity.BLOCKER,
                    title="Rights status insufficient",
                    explanation=(
                        f"Requested channel {channel} requires '{required_rights.value}' rights, "
                        f"but the asset is marked '{asset.rights_status.value}'."
                    ),
                    asset_id=asset.asset_id,
                    remediation=asset.rights_note,
                )
            )

        if asset.duration_seconds > max_duration:
            findings.append(
                PolicyFinding(
                    rule_id="FORMAT-001",
                    severity=Severity.WARNING,
                    title="Duration exceeds channel guidance",
                    explanation=(
                        f"The asset is {asset.duration_seconds}s; the configured {channel} guidance "
                        f"is {max_duration}s."
                    ),
                    asset_id=asset.asset_id,
                    remediation=f"Create a cut-down under {max_duration}s or choose another channel.",
                )
            )

        if asset.content_rating not in allowed_ratings:
            findings.append(
                PolicyFinding(
                    rule_id="ED-003",
                    severity=Severity.BLOCKER,
                    title="Content rating incompatible with channel",
                    explanation=(
                        f"The asset content rating '{asset.content_rating}' is not permitted on "
                        f"the requested {channel} channel."
                    ),
                    asset_id=asset.asset_id,
                    remediation="Choose a suitable asset or route to editorial review.",
                )
            )

        return findings

    @staticmethod
    def _rights_rank(status: RightsStatus) -> int:
        return {
            RightsStatus.UNKNOWN: 0,
            RightsStatus.RESTRICTED: 1,
            RightsStatus.CLEARED: 2,
        }[status]
