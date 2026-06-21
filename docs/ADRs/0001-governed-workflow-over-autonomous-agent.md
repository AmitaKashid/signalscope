# ADR 0001: Use a Governed Workflow Rather Than an Autonomous Publishing Agent

- **Status:** Accepted
- **Date:** 2026-06-21

## Context

The system recommends audiovisual assets for editorial and distribution purposes. The domain includes rights, policy, audience, and reputational constraints. A free-form agent that dynamically chooses tools and actions can be difficult to audit and can fail open when it sees ambiguous instructions.

## Decision

Use an explicit LangGraph state graph with fixed stages:

1. request safety;
2. brief parsing;
3. retrieval;
4. policy validation;
5. ranking;
6. explanation;
7. quality gate;
8. human approval.

No node is allowed to publish content. Policy eligibility remains deterministic.

## Consequences

### Positive

- tool usage is inspectable;
- testing is easier;
- policy owners can review rules independently;
- prompt injection is contained before tool execution;
- clients can understand the decision path;
- human approval is structurally required.

### Trade-offs

- less apparent autonomy;
- new workflow needs require graph changes;
- policy rules must be maintained explicitly;
- complex multi-step tasks may require additional nodes.

## Alternatives considered

### Fully autonomous ReAct agent

Rejected because tool selection, planning, and final action boundaries would be harder to control in a rights-sensitive editorial workflow.

### Single RAG prompt

Rejected because retrieval and generated language alone do not reliably enforce channel rights, duration, rating, or human approval constraints.
