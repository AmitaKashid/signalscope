# Evaluation Protocol

## Objective

SignalScope evaluates the full decision workflow, not only final-language quality. The core question is:

> Does the system retrieve suitable assets, reject ineligible ones, attach evidence, complete its governed stages, and remain responsive enough for editorial use?

## Golden dataset

The repository includes a small synthetic golden set in:

```text
data/demo/evaluation_tasks.json
```

Each task includes:

- a natural-language editorial request;
- expected asset identifiers;
- disallowed asset identifiers;
- requested channels.

The dataset deliberately includes a rights-safety case where a semantically relevant asset must not be recommended because its rights are unresolved.

## Metrics

| Metric | Definition | Failure mode addressed |
|---|---|---|
| Recall@3 | Fraction of expected assets present in the top 3 eligible results | Relevant assets are missed |
| Precision@3 | Fraction of top 3 results that are expected | Search returns noisy alternatives |
| Evidence coverage | Fraction of eligible recommendations with retained evidence | Fluent but unsupported conclusions |
| Valid trace rate | Completed trace events divided by all trace events | Workflow stages silently fail |
| Disallowed recommendation count | Disallowed assets appearing among recommended output | Policy guardrails fail open |
| Latency | End-to-end local runtime per task | Workflow is impractical interactively |

## Run locally

```bash
make evaluate
```

Or:

```bash
python scripts/run_evaluations.py --output-dir artifacts/evaluations
```

The generated JSON report contains aggregate metrics and per-case details. Reports are intentionally excluded from source control because they are generated artifacts.

## Evaluation assertions for CI

CI should fail when:

- a disallowed asset appears in eligible results;
- mean evidence coverage falls below the defined threshold;
- trace stages fail unexpectedly;
- critical golden tasks no longer retrieve their expected asset;
- a policy change changes decision behavior without reviewer sign-off.

## Human evaluation rubric

Automated scores do not replace editorial assessment. A reviewer should rate a stratified sample on:

| Dimension | Question | Scale |
|---|---|---|
| Editorial relevance | Would this help a real editor select media? | 1–5 |
| Evidence usefulness | Do excerpts and metadata support the recommendation? | 1–5 |
| Explanation clarity | Can a non-engineer understand why the result was selected? | 1–5 |
| Rights safety | Are blocked or restricted assets handled correctly? | Pass / fail |
| Counterfactual utility | Does the system state a useful remediation path? | 1–5 |
| Operational trust | Would the reviewer know when to override the system? | 1–5 |

## Model-policy evaluation extension

When an approved LLM provider is configured, evaluate each candidate under an identical frozen context:

- same task set;
- same retrieved evidence;
- same structured output schema;
- same policy gate;
- same temperature;
- same maximum tokens;
- same timeout;
- same reviewer rubric.

Compare:

- groundedness;
- citation precision and completeness;
- recommendation stability;
- latency;
- estimated cost per workflow;
- privacy and deployment constraints;
- tool-call validity.

Do not treat a higher language-model score as sufficient evidence for production selection. The selected policy must fit operational, privacy, and editorial-control requirements.
