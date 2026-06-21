"""Composition root for the API process."""

from __future__ import annotations

from dataclasses import dataclass

from signalscope.agents.workflow import MediaWorkflowService
from signalscope.application.approval_store import ApprovalStore
from signalscope.application.brief_parser import BriefParser
from signalscope.application.explainability import ExplanationService
from signalscope.application.quality_gate import QualityGate
from signalscope.application.ranking import RecommendationRanker
from signalscope.application.workflow_store import WorkflowStore
from signalscope.core.config import Settings
from signalscope.infrastructure.catalog_repository import CatalogRepository
from signalscope.infrastructure.hybrid_retriever import HybridRetriever
from signalscope.infrastructure.llm_client import build_narrative_client
from signalscope.infrastructure.policy_engine import PolicyEngine


@dataclass(frozen=True)
class ApplicationContainer:
    """All process-scoped services used by API routes."""

    settings: Settings
    catalog: CatalogRepository
    workflow: MediaWorkflowService
    approvals: ApprovalStore
    workflows: WorkflowStore


def build_container(settings: Settings) -> ApplicationContainer:
    """Wire adapters and use cases in one place for testability and clarity."""

    catalog = CatalogRepository(settings.data_dir)
    retriever = HybridRetriever(catalog)
    policy_engine = PolicyEngine(settings.data_dir)
    workflow = MediaWorkflowService(
        settings=settings,
        brief_parser=BriefParser(),
        retriever=retriever,
        policy_engine=policy_engine,
        ranker=RecommendationRanker(),
        explanation_service=ExplanationService(),
        quality_gate=QualityGate(settings.minimum_evidence_coverage),
        narrative_client=build_narrative_client(settings),
    )
    return ApplicationContainer(
        settings=settings,
        catalog=catalog,
        workflow=workflow,
        approvals=ApprovalStore(),
        workflows=WorkflowStore(),
    )
