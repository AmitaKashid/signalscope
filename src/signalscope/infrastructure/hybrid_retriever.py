"""A transparent hybrid retriever with deterministic dense and lexical scoring.

The local implementation intentionally avoids opaque hosted services so the repository
can run in demo mode. Interfaces are kept narrow so a pgvector or Qdrant adapter can
replace this class without changing agent workflow code.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from signalscope.domain.models import Asset, CampaignBrief, EvidenceReference
from signalscope.infrastructure.catalog_repository import CatalogRepository
from signalscope.infrastructure.text import tokenize


@dataclass(frozen=True)
class RetrievedAsset:
    """Asset plus transparent retrieval contributions."""

    asset: Asset
    lexical_score: float
    semantic_score: float
    metadata_score: float
    final_score: float
    evidence: list[EvidenceReference]


class HashEmbeddingModel:
    """Stable hashing-vector encoder for local development and unit testing.

    This is not a semantic model suitable for production. It exists so the complete
    workflow remains runnable without GPU hardware, API keys, or a vector database.
    The `Retriever` interface is designed for a sentence-transformer replacement.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def encode(self, text: str) -> list[float]:
        """Create a normalized sparse hashing vector."""

        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def cosine(left: list[float], right: list[float]) -> float:
        """Compute cosine similarity for pre-normalized vectors."""

        if len(left) != len(right):
            raise ValueError("Embedding vectors must have the same dimension.")
        return sum(a * b for a, b in zip(left, right, strict=True))


class HybridRetriever:
    """Rank media assets with lexical, deterministic-vector, and metadata signals."""

    def __init__(
        self, repository: CatalogRepository, embedding_model: HashEmbeddingModel | None = None
    ) -> None:
        self._repository = repository
        self._embedding_model = embedding_model or HashEmbeddingModel()
        self._asset_vectors: dict[str, list[float]] = {}
        self._document_frequency: Counter[str] = Counter()
        self._avg_document_length: float = 1.0
        self._indexed = False

    def index(self) -> None:
        """Build lightweight in-memory retrieval statistics."""

        if self._indexed:
            return

        assets = self._repository.list_assets()
        document_lengths: list[int] = []
        for asset in assets:
            document = self._asset_document(asset)
            tokens = tokenize(document)
            document_lengths.append(max(len(tokens), 1))
            self._document_frequency.update(set(tokens))
            self._asset_vectors[asset.asset_id] = self._embedding_model.encode(document)

        self._avg_document_length = sum(document_lengths) / max(len(document_lengths), 1)
        self._indexed = True

    def search(self, brief: CampaignBrief, limit: int) -> list[RetrievedAsset]:
        """Retrieve candidate assets and preserve enough detail for auditability."""

        self.index()
        query = self._query_text(brief)
        query_tokens = tokenize(query)
        query_vector = self._embedding_model.encode(query)
        all_assets = self._repository.list_assets()
        candidate_rows: list[RetrievedAsset] = []

        for asset in all_assets:
            lexical = self._bm25(query_tokens, self._asset_document(asset), len(all_assets))
            semantic = max(
                self._embedding_model.cosine(query_vector, self._asset_vectors[asset.asset_id]), 0.0
            )
            metadata = self._metadata_score(asset, brief)

            # Hybrid weighting is intentionally explicit and can be surfaced to reviewers.
            final_score = round(0.45 * lexical + 0.40 * semantic + 0.15 * metadata, 4)
            evidence = self._evidence_for(asset, query_tokens, final_score)
            candidate_rows.append(
                RetrievedAsset(
                    asset=asset,
                    lexical_score=round(lexical, 4),
                    semantic_score=round(semantic, 4),
                    metadata_score=round(metadata, 4),
                    final_score=final_score,
                    evidence=evidence,
                )
            )

        return sorted(candidate_rows, key=lambda row: row.final_score, reverse=True)[:limit]

    def _bm25(self, query_tokens: list[str], document: str, corpus_size: int) -> float:
        """Calculate a normalized BM25 score using local corpus statistics."""

        document_tokens = tokenize(document)
        term_counts = Counter(document_tokens)
        document_length = max(len(document_tokens), 1)
        k1 = 1.5
        b = 0.75
        raw = 0.0

        for term in set(query_tokens):
            frequency = term_counts[term]
            if frequency == 0:
                continue
            inverse_document_frequency = math.log(
                1
                + (corpus_size - self._document_frequency[term] + 0.5)
                / (self._document_frequency[term] + 0.5)
            )
            denominator = frequency + k1 * (1 - b + b * document_length / self._avg_document_length)
            raw += inverse_document_frequency * (frequency * (k1 + 1) / denominator)

        # Scores are bounded for dashboard display and downstream factor blending.
        return min(raw / 8.0, 1.0)

    @staticmethod
    def _asset_document(asset: Asset) -> str:
        transcript_text = " ".join(segment.text for segment in asset.transcript)
        return " ".join(
            [
                asset.title,
                asset.synopsis,
                asset.visual_summary,
                " ".join(asset.topics),
                " ".join(asset.audience_tags),
                " ".join(asset.keyframe_tags),
                transcript_text,
            ]
        )

    @staticmethod
    def _query_text(brief: CampaignBrief) -> str:
        return " ".join(
            [
                brief.campaign_goal,
                brief.raw_request,
                brief.target_audience,
                " ".join(brief.topics),
                " ".join(channel.value.replace("_", " ") for channel in brief.requested_channels),
            ]
        )

    @staticmethod
    def _metadata_score(asset: Asset, brief: CampaignBrief) -> float:
        """Score deterministic metadata fit independently from content similarity."""

        audience_terms = set(tokenize(brief.target_audience))
        asset_audience = set(tokenize(" ".join(asset.audience_tags)))
        audience_score = len(audience_terms & asset_audience) / max(len(audience_terms), 1)

        requested_channels = set(brief.requested_channels)
        channel_score = (
            len(requested_channels & set(asset.allowed_channels)) / len(requested_channels)
            if requested_channels
            else 0.8
        )
        language_score = 1.0 if brief.preferred_language in (None, asset.language) else 0.0

        duration_score = 1.0
        if brief.maximum_duration_seconds is not None:
            duration_score = (
                1.0 if asset.duration_seconds <= brief.maximum_duration_seconds else 0.25
            )

        return (
            0.35 * audience_score
            + 0.35 * channel_score
            + 0.15 * language_score
            + 0.15 * duration_score
        )

    @staticmethod
    def _evidence_for(
        asset: Asset, query_tokens: list[str], retrieval_score: float
    ) -> list[EvidenceReference]:
        """Select the most query-relevant transcript evidence plus metadata evidence."""

        evidence: list[EvidenceReference] = []
        transcript_scores: list[tuple[int, int]] = []
        for index, segment in enumerate(asset.transcript):
            overlap = len(set(query_tokens) & set(tokenize(segment.text)))
            transcript_scores.append((overlap, index))

        for _, index in sorted(transcript_scores, reverse=True)[:2]:
            segment = asset.transcript[index]
            evidence.append(
                EvidenceReference(
                    evidence_id=f"{asset.asset_id}:{segment.segment_id}",
                    asset_id=asset.asset_id,
                    evidence_type="transcript",
                    excerpt=segment.text,
                    source_label=f"{asset.title} transcript",
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    retrieval_score=round(retrieval_score, 4),
                    citation_url=asset.source_url,
                )
            )

        evidence.append(
            EvidenceReference(
                evidence_id=f"{asset.asset_id}:metadata",
                asset_id=asset.asset_id,
                evidence_type="metadata",
                excerpt=(
                    f"Topics: {', '.join(asset.topics)} | Audience: {', '.join(asset.audience_tags)} | "
                    f"Rights: {asset.rights_status.value}"
                ),
                source_label=f"{asset.title} catalog metadata",
                retrieval_score=round(retrieval_score, 4),
                citation_url=asset.source_url,
            )
        )
        return evidence


def freshness_score(published_at: datetime) -> float:
    """Map recency to a bounded score with a half-life suitable for editorial catalogs."""

    age_days = max((datetime.now(timezone.utc) - published_at).days, 0)
    return round(math.exp(-age_days / 180), 4)
