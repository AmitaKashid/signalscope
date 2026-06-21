# Five-Minute Demo Script

## 0:00–0:35 — Context

> Editorial and media teams need to find the right asset quickly, but recommendation quality depends on more than semantic similarity. Rights, channel constraints, evidence, and human accountability are part of the decision. SignalScope is designed as a governed workflow that makes each of those steps visible.

## 0:35–1:10 — Submit a real brief

Enter:

> Find three short climate-awareness clips for 18–34 year olds. Recommend what should go to social media and the media library, with evidence and rights-safe alternatives.

Point out the channel constraints and maximum recommendation limit.

## 1:10–1:50 — Explain the workflow

Show the result trace:

1. request safety;
2. brief interpretation;
3. hybrid media retrieval;
4. policy validation;
5. transparent ranking;
6. evidence and counterfactuals;
7. quality gate;
8. human approval.

Emphasize that each stage is explicit and audited. The system is not an unconstrained agent deciding how to act.

## 1:50–3:05 — Inspect a recommendation

Open the top recommendation and show:

- factor-level score;
- transcript timestamp;
- catalog metadata evidence;
- rights status;
- channel eligibility;
- counterfactual explanation.

Explain that the recommendation is actionable because an editor can see why it fits, not merely read a generated paragraph.

## 3:05–3:45 — Inspect an exclusion

Open a rights-restricted or rights-unknown candidate.

Explain:

> SignalScope keeps unsafe alternatives visible instead of silently dropping them. The editor sees exactly why an asset was excluded and what needs to change, such as a rights clearance or a shorter channel-specific cut.

## 3:45–4:25 — Human approval

Use the approval controls.

Explain:

> The agent does not publish content. The final decision is recorded with reviewer accountability, preserving editorial control.

## 4:25–5:00 — Engineering depth

Close with:

> Under the interface, the project includes LangGraph orchestration, MCP servers for catalog and policy tools, FastAPI contracts, evaluation metrics, test coverage, Docker, GitHub Actions, and Terraform for a GCP Cloud Run deployment. It is a complete product-engineering system rather than a standalone RAG demo.
