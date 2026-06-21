# Reference Local Validation Results

This file records one reference execution of the synthetic demo catalog on **2026-06-21**. These numbers are not production performance claims and must be regenerated after retrieval, policy, or evaluation changes.

## Quality checks

| Check | Result |
|---|---|
| Python syntax compilation | Passed |
| Ruff lint and formatting | Passed |
| mypy strict type check | Passed |
| Pytest suite | 10 passed |
| FastAPI smoke test | Passed |
| Next.js production build | Passed |
| MCP tool smoke test | Passed |

## Golden-set evaluation

| Metric | Reference value |
|---|---:|
| Golden tasks | 5 |
| Mean Recall@3 | 1.0000 |
| Mean Precision@3 | 0.4667 |
| Mean evidence coverage | 1.0000 |
| Mean valid trace rate | 1.0000 |
| Disallowed recommendation count | 0 |
| Mean local end-to-end latency | 5.34 ms |

## Interpretation

- Recall and guardrail results show expected behavior on the intentionally small synthetic golden set.
- Precision is lower than recall because the demo returns several policy-eligible alternatives beyond the expected items. This is a useful improvement target for stronger reranking or tighter editorial-query constraints.
- Local latency is not representative of production performance because the demo uses an in-memory synthetic catalog, deterministic local retrieval, and no remote model call.
- Production acceptance should add human editorial evaluation, realistic media-scale latency testing, model-policy comparisons, and rights-source integration tests.
