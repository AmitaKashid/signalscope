# Contributing

## Development standards

- Keep domain logic independent from FastAPI and framework concerns.
- Add typed Pydantic models for externally visible data.
- Write deterministic tests for policy, retrieval, and quality-gate changes.
- Update the golden evaluation set when behavior changes intentionally.
- Do not add a tool that can publish, delete, or change rights state without a separate authorization design.
- Keep policy rules explainable and reviewable by non-engineering stakeholders.

## Pull request checklist

- [ ] Tests added or updated.
- [ ] `make lint` passes.
- [ ] `make typecheck` passes.
- [ ] `make test` passes.
- [ ] `make evaluate` passes.
- [ ] Documentation reflects behavioral changes.
- [ ] No secrets, synthetic data only, and no proprietary media assets are committed.
- [ ] Any policy change includes an explicit reviewer rationale.

## Commit style

Use concise imperative commits:

```text
feat: add rights-window policy adapter
fix: block unknown rights on external channels
test: add injection guard golden case
docs: clarify production vector-store path
```
