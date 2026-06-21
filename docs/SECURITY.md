# Security and Governance

## Scope

SignalScope is a demonstration system. Its security model illustrates the controls required for an agentic media workflow but does not replace an organization-specific threat model, legal review, data-protection assessment, identity architecture, or incident process.

## Threat model

| Threat | Control in repository | Production extension |
|---|---|---|
| Prompt injection | Pre-retrieval pattern check, typed workflow nodes, deterministic policy gate | Dedicated injection classifier, adversarial test suite, review queue |
| Unauthorized publication | No publication tool exists; human approval only records a decision | Separate publish service with RBAC, workflow state checks, dual control |
| Rights violation | Channel authorization and rights status are validated before recommendation | Rights-source integration, territory/time-window checks, legal review audit |
| Evidence fabrication | Recommendations include evidence objects and coverage checks | Citation verification against immutable source snapshots |
| Unsafe tool use | MCP tools are read-only and domain-scoped | Signed tool registry, allowlists, authn/authz, rate limits |
| Secret exposure | Environment variables are used only for local development | Secret Manager, workload identity, rotation, no secrets in client |
| Cross-tenant leakage | Not applicable to synthetic demo catalog | Tenant IDs, row-level security, separate vector namespaces |
| Workflow tampering | Trace retained in response output | Immutable audit log, event signing, retention controls |

## Guardrail order

1. Validate the request for instruction-like unsafe patterns.
2. Parse into a typed brief.
3. Retrieve candidates.
4. Apply rights, duration, rating, and channel rules.
5. Exclude blocked candidates.
6. Attach evidence and counterfactual explanations.
7. Run the quality gate.
8. Require human decision.

The order matters: policy checks should not be delegated to a language model, and downstream narrative text should not bypass earlier constraints.

## MCP safeguards

The included MCP servers are intentionally read-only.

### Not allowed

- publication;
- rights-state modification;
- policy override;
- external web requests;
- data deletion;
- user identity management;
- access-token generation.

### Required in a production integration

- OAuth or workload identity;
- service-specific authorization;
- tool approval policy;
- request/response schema validation;
- rate limiting;
- structured audit logs;
- allowlisted resources;
- egress restrictions;
- change-control review for new tools.

## Privacy principles

A real deployment should define:

- what media metadata and transcripts can be indexed;
- whether content contains personal data;
- whether model providers may process content;
- data residency and retention requirements;
- legal basis and consent requirements where relevant;
- redaction or pseudonymization procedures;
- audit and deletion processes;
- acceptable-use boundaries for generative summaries.

## Incident readiness checklist

- [ ] Assign owner for rights policy source of truth.
- [ ] Define audit-log retention period.
- [ ] Define a rollback plan for policy changes.
- [ ] Alert on policy-blocker bypass attempts.
- [ ] Alert on elevated tool errors and trace failures.
- [ ] Document escalation to editorial, legal, security, and platform owners.
- [ ] Conduct adversarial prompt-injection exercises.
- [ ] Re-run golden-set regression after every policy or retriever change.
