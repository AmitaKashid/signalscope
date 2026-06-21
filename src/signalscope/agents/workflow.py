"""Governed LangGraph workflow for explainable media recommendations."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from signalscope.agents.state import MediaWorkflowState
from signalscope.application.brief_parser import BriefParser
from signalscope.application.explainability import ExplanationService
from signalscope.application.quality_gate import QualityGate
from signalscope.application.ranking import RecommendationRanker
from signalscope.core.config import Settings
from signalscope.domain.enums import RecommendationDecision, Severity, WorkflowStatus
from signalscope.domain.models import CampaignRequest, DecisionBrief, QualityGateResult
from signalscope.infrastructure.hybrid_retriever import HybridRetriever
from signalscope.infrastructure.llm_client import NarrativeClient
from signalscope.infrastructure.policy_engine import PolicyEngine
from signalscope.infrastructure.tracing import TraceRecorder


class MediaWorkflowService:
    """Coordinates narrow, inspectable nodes rather than an unconstrained autonomous agent.

    The graph deliberately separates interpretation, retrieval, rights validation,
    ranking, explanation, and approval gating. Every decision is retained in the
    response trace so stakeholders can inspect how a recommendation was formed.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        brief_parser: BriefParser,
        retriever: HybridRetriever,
        policy_engine: PolicyEngine,
        ranker: RecommendationRanker,
        explanation_service: ExplanationService,
        quality_gate: QualityGate,
        narrative_client: NarrativeClient,
    ) -> None:
        self._settings = settings
        self._brief_parser = brief_parser
        self._retriever = retriever
        self._policy_engine = policy_engine
        self._ranker = ranker
        self._explanation_service = explanation_service
        self._quality_gate = quality_gate
        self._narrative_client = narrative_client
        self._graph: Any = self._build_graph()

    def run(self, request: CampaignRequest) -> DecisionBrief:
        """Execute the graph and return a complete, approval-ready decision brief."""

        workflow_id = str(uuid4())
        trace_recorder = TraceRecorder(workflow_id)
        initial_state: MediaWorkflowState = {
            "workflow_id": workflow_id,
            "raw_request": request.request,
            "explicit_channels": request.requested_channels,
            "maximum_results": min(request.maximum_results, self._settings.max_recommendations),
            "trace_recorder": trace_recorder,
            "diagnostics": {},
        }
        final_state = cast(MediaWorkflowState, self._graph.invoke(initial_state))
        return final_state["decision_brief"]

    def _build_graph(self) -> Any:
        graph = StateGraph(MediaWorkflowState)
        graph.add_node("guard_request", self._guard_request)
        graph.add_node("interpret_brief", self._interpret_brief)
        graph.add_node("retrieve_assets", self._retrieve_assets)
        graph.add_node("validate_policy", self._validate_policy)
        graph.add_node("rank_assets", self._rank_assets)
        graph.add_node("explain_decisions", self._explain_decisions)
        graph.add_node("quality_gate", self._evaluate_quality)
        graph.add_node("assemble_decision", self._assemble_decision)
        graph.add_node("assemble_blocked_decision", self._assemble_blocked_decision)

        graph.add_edge(START, "guard_request")
        graph.add_conditional_edges(
            "guard_request",
            self._route_after_guard,
            {"continue": "interpret_brief", "blocked": "assemble_blocked_decision"},
        )
        graph.add_edge("interpret_brief", "retrieve_assets")
        graph.add_edge("retrieve_assets", "validate_policy")
        graph.add_edge("validate_policy", "rank_assets")
        graph.add_edge("rank_assets", "explain_decisions")
        graph.add_edge("explain_decisions", "quality_gate")
        graph.add_edge("quality_gate", "assemble_decision")
        graph.add_edge("assemble_decision", END)
        graph.add_edge("assemble_blocked_decision", END)
        return graph.compile()

    def _guard_request(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        with trace.span("guard_request", tool="editorial_policy.validate_request"):
            findings = self._policy_engine.validate_request(state["raw_request"])
            blocked = any(finding.severity is Severity.BLOCKER for finding in findings)
            return {
                "request_findings": findings,
                "blocked": blocked,
                "diagnostics": {"request_findings": len(findings)},
            }

    @staticmethod
    def _route_after_guard(state: MediaWorkflowState) -> str:
        return "blocked" if state.get("blocked", False) else "continue"

    def _interpret_brief(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        with trace.span("interpret_brief", tool="brief_parser.parse"):
            brief = self._brief_parser.parse(
                raw_request=state["raw_request"],
                explicit_channels=state.get("explicit_channels", []),
                request_id=state["workflow_id"],
            )
            return {
                "brief": brief,
                "diagnostics": {
                    **state.get("diagnostics", {}),
                    "topics": len(brief.topics),
                    "channels": len(brief.requested_channels),
                },
            }

    def _retrieve_assets(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        brief = state["brief"]
        with trace.span(
            "retrieve_assets",
            tool="media_catalog.search_assets",
            candidate_limit=self._settings.retrieval_candidate_limit,
        ):
            candidates = self._retriever.search(brief, self._settings.retrieval_candidate_limit)
            return {
                "candidates": candidates,
                "diagnostics": {**state.get("diagnostics", {}), "candidate_count": len(candidates)},
            }

    def _validate_policy(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        brief = state["brief"]
        with trace.span("validate_policy", tool="editorial_policy.validate_distribution"):
            findings = {
                candidate.asset.asset_id: self._policy_engine.evaluate_asset(candidate.asset, brief)
                for candidate in state["candidates"]
            }
            blocker_count = sum(
                1
                for asset_findings in findings.values()
                for finding in asset_findings
                if finding.severity is Severity.BLOCKER
            )
            return {
                "policy_findings_by_asset": findings,
                "diagnostics": {**state.get("diagnostics", {}), "policy_blockers": blocker_count},
            }

    def _rank_assets(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        with trace.span("rank_assets", tool="transparent_ranker.score_candidates"):
            ranked_candidates = self._ranker.rank(
                brief=state["brief"],
                candidates=state["candidates"],
                policy_findings_by_asset=state["policy_findings_by_asset"],
            )
            return {"ranked_candidates": ranked_candidates}

    def _explain_decisions(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        with trace.span("explain_decisions", tool="explanation_engine.generate"):
            recommendations = [
                self._explanation_service.enrich(state["brief"], item.recommendation)
                for item in state["ranked_candidates"]
            ]
            return {"recommendations": recommendations}

    def _evaluate_quality(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        with trace.span("quality_gate", tool="quality_gate.evaluate"):
            quality_gate = self._quality_gate.evaluate(state["recommendations"])
            return {"quality_gate": quality_gate}

    def _assemble_decision(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        with trace.span("assemble_decision", tool="narrative_client.summarize"):
            recommendations = state["recommendations"]
            selected = [
                recommendation
                for recommendation in recommendations
                if recommendation.decision is RecommendationDecision.RECOMMEND
            ][: state["maximum_results"]]
            excluded = [
                recommendation
                for recommendation in recommendations
                if recommendation.decision is RecommendationDecision.EXCLUDE
            ]
            summary = self._narrative_client.summarize(state["brief"], selected)

        # Snapshot only after the final trace span has completed, otherwise the response
        # would misleadingly expose the assembly node as still in progress.
        decision_brief = DecisionBrief(
            workflow_id=state["workflow_id"],
            status=state["quality_gate"].status,
            brief=state["brief"],
            executive_summary=summary,
            recommendations=selected,
            excluded_assets=excluded,
            quality_gate=state["quality_gate"],
            trace=trace.snapshot(),
        )
        return {"decision_brief": decision_brief}

    def _assemble_blocked_decision(self, state: MediaWorkflowState) -> dict[str, Any]:
        trace = state["trace_recorder"]
        with trace.span("assemble_blocked_decision", tool="quality_gate.block_request"):
            brief = self._brief_parser.parse(
                raw_request=state["raw_request"],
                explicit_channels=state.get("explicit_channels", []),
                request_id=state["workflow_id"],
            )
            quality_gate = QualityGateResult(
                status=WorkflowStatus.BLOCKED,
                evidence_coverage=0.0,
                unsupported_claim_count=0,
                blocker_count=len(state.get("request_findings", [])),
                notes=[finding.explanation for finding in state.get("request_findings", [])],
            )

        decision_brief = DecisionBrief(
            workflow_id=state["workflow_id"],
            status=WorkflowStatus.BLOCKED,
            brief=brief,
            executive_summary=(
                "The request was blocked before retrieval because it contains an instruction-like "
                "pattern that could undermine the workflow's policy and evidence safeguards."
            ),
            recommendations=[],
            excluded_assets=[],
            quality_gate=quality_gate,
            trace=trace.snapshot(),
        )
        return {"decision_brief": decision_brief}
