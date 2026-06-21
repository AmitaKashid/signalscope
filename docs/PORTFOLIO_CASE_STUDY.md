# Portfolio Case Study: SignalScope

## Problem

Editorial teams often need to identify media assets for specific audiences and channels under time pressure. Basic similarity search can surface relevant content but does not answer whether an asset is rights-cleared, format-compatible, evidence-supported, or safe to recommend.

## Solution

SignalScope is an explainable media-intelligence copilot that transforms a campaign brief into a structured, approval-ready recommendation. It combines:

- hybrid retrieval across metadata, transcript text, topical tags, audience labels, and visual descriptions;
- a LangGraph workflow with controlled stages;
- MCP-ready media and policy tools;
- deterministic rights and channel rules;
- transparent multi-factor ranking;
- evidence excerpts and timestamp citations;
- counterfactual explanations;
- a human approval gate;
- a versioned evaluation harness.

## Architectural decisions

### Governed workflow over autonomous agent

The system uses small typed nodes with explicit transitions. This makes tool usage and safety checks inspectable.

### Deterministic policy engine

Rights, distribution channel, rating, and duration decisions are rules-based. A generative model may assist with narrative summaries but cannot override eligibility.

### Explainability as a product feature

The UI shows evidence, factor scores, exclusions, policy findings, and what would change the decision outcome.

### Offline runnable core

The repository includes a synthetic catalog and local deterministic retrieval so reviewers can run the full workflow without paid APIs or cloud credentials.

## Technical stack

| Layer | Technology | Reason |
|---|---|---|
| API | FastAPI + Pydantic | Typed, documented async-friendly Python service contracts |
| Workflow | LangGraph | Explicit state graph, controlled nodes, conditional routing |
| Tools | MCP | Reusable standardized tool contracts for catalog and policy access |
| Retrieval | Hybrid lexical + local vector scoring | Runnable demo with a direct path to production vector stores |
| Frontend | Next.js + TypeScript | Responsive client-facing decision workspace |
| Evaluation | Pytest + custom golden-set harness | Reproducible task, guardrail, trace, and latency checks |
| Deployment | Docker + Cloud Run + Terraform | Managed production path with infrastructure as code |
| Quality | Ruff, mypy, pytest, GitHub Actions | Code quality and regression controls |

## Impact framing

This project is intentionally a technical prototype. It does not claim real-world customer impact. Its value is evidence that an engineer can design and implement:

- agentic systems that use tools safely;
- RAG systems that preserve evidence;
- explainable decision workflows;
- cloud-ready, monitored, evaluated APIs;
- media-domain functionality without sacrificing editorial control.
