---
name: hallx-conventions
description: >
  Binding engineering conventions for the hallx codebase. Enforced by reviewer
  before merges. Read this BEFORE writing code inside hallx: style, naming,
  typing, docstrings, sync/async, test conventions, git hygiene, and the public
  API contract. Conventional.md is the normative file; skills.md is the mental
  model.
---

# Conventional: how hallx code must be written

## Style and language

- Python 3.9+ compatible, with type hints on **every** parameter and return of
  every public function. No `Any` leaking from public signatures; private
  helpers may loosen internally. `Any` is permitted at documented raw-input
  normalization boundaries (`Hallx.check(response=...)`,
  `check_tool_call(tool_calls=...)`) but must not appear on typed outputs or
  structured APIs.
- Line length hard limit **88 characters** (project target 84-88). Break long
  definitions across lines.
- f-strings preferred; no `%`-formatting.
- Private helpers are underscore-prefixed; the internal wiring never appears in
  the public API surface.
- Imports: stdlib, then third-party, then `hallx.*`, each group alphabetical.
- Docstrings: module docstring at the top of every file; a docstring on every
  public function/class; examples in `Example::` blocks for non-obvious usage.

## Public API contract

- Every user-facing symbol is re-exported from `hallx/__init__.py`, and
  `__all__` is alphabetical.
- Every public result is a **frozen dataclass** or **Protocol** defined in
  `hallx/types.py`. Never return raw dicts from a public API.
- For every sync function `check_x`, provide an async twin `check_x_async` with
  the same signature (minus the sync-only helpers). No sync-only public API
  unless it is intrinsically blocking.
- Optional backends (NLI, embeddings) import **lazily inside the function** so
  the core install stays importable with only jsonschema, rapidfuzz, requests.
- Optional-provider extras must be declared in `pyproject.toml` under
  `[project.optional-dependencies]` (e.g. `hallx[nli]`, `hallx[dev]`).

## Naming and typing

| Thing | Pattern |
|---|---|
| Result dataclasses | `*Result` — `HallxResult`, `ClaimGroundingResult`, `ToolCallResult` |
| Per-item verdicts | `*Verdict` — `ToolCallVerdict` |
| Verifier default | `FaithfulnessVerifier.verify(premise, hypothesis) -> float`; optional `averify` |
| Sync/async twins | `check_claim_grounding` + `check_claim_grounding_async` |
| Private helpers | leading `_`, snake_case (`_best_evidence`) |
| Claim status | lowercase strings: `extracted`, `supported`, `weak`, `unsupported`, `filtered` |
| Adapter protocol | `generate(prompt, system_prompt=None) -> str` and `agenerate(...) -> str` |

## Precision on scores

- Every score is `float` in `[0.0, 1.0]`, clamped via
  `max(0.0, min(1.0, value))` at every assignment edge.
- `combine_scores` is the single aggregation point; weights come from profiles
  (`fast`/`balanced`/`strict`) or user overrides via `resolve_weights`.
- `risk_level_from_confidence`: `>= 0.7 → low`, `>= 0.4 → medium`,
  `else → high`. Any scoring change can flip risk_level — rerun the suite.
- Skipped checks (`no context`, `no model`) must NOT score a confident 1.0 —
  `_apply_skip_penalty` discounts them and appends a `"penalized (…)"` issue.
- Adding a new check means adding a component key to the `scores` dict and
  keeping `weights` summing to `1.0`.

## Test conventions

- One file per module: `tests/test_<module>.py` mirrors `hallx/<module>.py`.
- Kinds included: unit, edge, async, strict/exception (`pytest.raises`),
  integration sample. Cover at least one empty/blank input, one threshold
  boundary, one sync and one async path per new function.
- Tests are deterministic: no network, no randomness, no real adapters. Use
  `llm_callable`/stub verifiers instead.
- Assert observed behavior (typed dataclass fields + status codes), not internal
  implementation values.
- Async is runnable under pytest-asyncio (`asyncio_mode = auto`); keep files
  that also run with plain `asyncio.run` inside the test body so the test
  suite is not fragile when the plugin is missing.
- `samples/*.py` are runnable demos that print to stdout; they are not the
  assertion target for tests.

## Git hygiene

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
  `test:`, `perf:`, `style:`. Scope optional, e.g. `feat(toolcalls):` or
  `fix(grounding):`.
- One purpose per commit; clean unrelated context; add tests with the code.
- Never commit secrets; respect `.gitignore`; never force-push.
- Commit only when explicitly asked; never stage unrelated files.
- Update `CHANGELOG.md` and the README feature list with user-visible changes.

## Ship checklist (do in order)

1. `python -m py_compile` the changed files.
2. `python -m pytest -q` — green.
3. Add/refresh `tests/test_<module>.py` with deterministic coverage.
4. Run touched `samples/*.py` (`PYTHONPATH=. python samples/...`).
5. Update `README.md`, `.skills/*.md`, and `CHANGELOG.md`.

Uphold the reference style in `hallx/` itself and the concise patterns in
`tests/` before making editorial judgement calls.