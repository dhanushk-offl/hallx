---
name: hallx-coding-agent
description: >
  Coding-agent skill for building on, modifying, and testing the hallx library.
  Use whenever a task touches the hallx package: adding a check, extending an
  adapter, wiring a new verifier, writing tests, tuning scoring, or fixing a bug.
  Covers modules and functions, conventions, the scoring logic, testing kinds,
  edge cases, efficiency, and knowledge transfer. Binding conventions live in
  .skills/conventional.md — read it before writing code.
---

# Skills: Building hallx with an Agent

This skill teaches a coding agent how to work inside the **hallx** codebase
correctly and quickly. Read `.skills/conventional.md` for the non-negotiable
style rules; this file is the mental model of how the library is organised, how
it scores, what the traps are, and how to test without guessing.

---

## 1. Repository map

| Path | Responsibility |
|---|---|
| `hallx/core.py` | `Hallx` API: `check`, `check_async`, `check_json`, `check_tool_call`, `assert_safe`, profiles & weights |
| `hallx/types.py` | All dataclasses/protocols: `HallxResult`, `SchemaValidationResult`, `Claim`, `ClaimGroundingResult`, `ToolCall`, `ToolCallVerdict`, `ToolCallResult`, `LLMAdapter`, errors |
| `hallx/schema.py` | JSON-Schema + null-injection validation (`validate_schema`, `validate_schema_detailed`) |
| `hallx/consistency.py` | Repeated-generation consistency (`check_consistency[_async]`) |
| `hallx/grounding.py` | Whole-response grounding + forbidden-source detection |
| `hallx/attribution.py` | **Claim-level** grounding: `extract_claims`, `check_claim_grounding[_async]`, evidence matching |
| `hallx/faithfulness/` | `FaithfulnessVerifier` protocol + `LocalNLIChecker` (optional `nli` extra) |
| `hallx/judge.py` | `GroundingJudge` — LLM-as-judge over any hallx adapter |
| `hallx/toolcalls.py` | `check_tool_call` / `score_tool_calls` — hallucinated-name & argument validation |
| `hallx/retry.py` | `build_recommendation` (action + suggested_temperature) |
| `hallx/scoring.py` | `combine_scores`, `resolve_weights`, `risk_level_from_confidence` |
| `hallx/calibration.py` | `FeedbackStore` — labelled feedback DB |
| `hallx/adapters/` | Provider adapters (OpenAI, Anthropic, Gemini, Grok, Ollama, Perplexity, OpenRouter, HuggingFace) |
| `hallx/utils/text.py` | `split_sentences`, `split_sentences_spans`, `is_assertive_sentence`, `normalize_text` |
| `tests/` | pytest suite, one file per module |
| `samples/` | Runnable end-to-end scripts |
| `.skills/` | This skill (skills.md + conventional.md) |

## Conventions map (`*.py` internal naming)

- Implementation helpers are private: underscore-prefixed (`_best_evidence`, `_filter_from_similarity`).
- Public leaf functions produce **typed dataclasses**; never raw dicts in the return value.
- Sync+async pairs always exist: `check_claim_grounding` + `check_claim_grounding_async`.
- Modules import from `hallx.types` for shared shapes, never redefine them locally.

---

## Keywords (search terms the codebase uses)

Use these exact words in grep/GLOB/searches — they are the vocabulary of the code:

`schema`, `consistency`, `grounding`, `claim`, `claims`, `evidence`, `supported`,
`weak`, `unsupported`, `filtered`, `verifier`, `verify`, `averify`, `judge`,
`premise`, `hypothesis`, `tool`, `tool_call`, `verdict`, `hallucinated`,
`confidence`, `risk_level`, `scores`, `recommendation`, `skip_penalty`,
`profile`, `weights`, `embedding`, `context_embeddings`, `fuzzy`,
`assertive_sentence`, `null_injection`, `forbidden_source`, `strict`,
`feedback`, `calibration`, `adapter`, `generate`, `agenerate`, `async`.

Common file-level search seeds:

- `grep -rn "check_claim_grounding" hallx/` — find all claim-grounding callers.
- `grep -rn "score_tool_calls" hallx/ tests/` — tool-call surface.
- `grep -rn "FaithfulnessVerifier" hallx/` — pluggable verifier wiring.
- `grep -rn "skip_penalty" hallx/core.py` — why confidence drops with no context.

---

## Scoring logic (the "why numbers move")

Everything returns a **confidence in `[0, 1]`**; higher = safer. `combine_scores`
mixes weighted components; `risk_level_from_confidence` maps to
`high`/`medium`/`low`. Three factors drag scores down:

1. **Per-issue penalties.** Each component converts issues into a bounded loss
   (e.g. `1.0 - 0.15 * len(issues)` for schema). More issues → more loss, capped at 0.
2. **Skip penalties.** When a check can't run (no context, no model), the
   component still participates but is discounted by `_apply_skip_penalty`.
3. **Strict mode.** `Hallx(strict=True)` turns a `high` **risk level** (low
   confidence, `< 0.4`) into a raised `HallxHighRiskError`. High risk is the
   low-confidence outcome — not high confidence. **Guard every changed path**:
   does the new code behave identically for `strict=False` (returns) and
   `strict=True` (raises)?

### Claim grounding (per-sentence)

`check_claim_grounding` splits the response into sentence spans, drops
non-assertive sentences (`filtered`), then per sentence picks the **best evidence
snippet** and maps similarity to status:

- `similarity >= supported_threshold (0.7)` → `supported`
- `>= weak_threshold (0.4)` → `weak`
- else → `unsupported`

Claim `status` values: `extracted` (from `extract_claims`), `supported`,
`weak`, `unsupported`, `filtered`.

Evidence ordering (per claim, in priority order):
1. **Verifier path** when `verifier` is truthy (NLI or LLM-judge) — most accurate.
2. **Embedding path** when `embedding_callable` (+ optional `context_embeddings`).
3. **Fuzzy text fallback** (partial ratio) — only when both above are absent.

### Tool-call validation

Per call: known name + schema-valid arguments → `ok`. Unknown name →
`unknown_tool` (confidence 0.0 for that call). Bad JSON → `malformed`. Schema
violation → `invalid_arguments`. Aggregate score penalises unknown tools harder
(`-0.25` each) so hallucination is clearly `block`-flagged. Recommendation action
is for the caller: `proceed` / `fix` / `block`.

---

## Kinds of testing

Run `python -m pytest tests/ -q` (asyncio tests need `pytest-asyncio`, the dev
extra). Follow the existing shape:

| Test kind | Canonical file | Rules |
|---|---|---|
| Unit (component) | `tests/test_scoring.py`, `tests/test_toolcalls.py` | Pure inputs → typed cells, exact pytest.approx asserts |
| Edge cases | inner of `tests/test_grounding.py` etc. | empty strings, missing context, `None`, empty tool list, zero vectors |
| Async | existing async tests in `test_scoring.py` / `test_consistency.py` | `await` or `asyncio.run` a helper; assert typed result |
| Strict / exception | `test_scoring.py::test_hallx_check_and_strict_mode` | `pytest.raises(HallxHighRiskError)` — never swallow |
| CLI-spec samples | `samples/*.py` | runnable; print with `print(...)`; import at top |
| Property-light | prefer | keep assertions on returned dataclass fields |

Never write tests that silently pass on `raise`; always `pytest.raises`.

When adding a new module, **add a test file immediately**: `tests/test_<module>.py`.

---

## Edge cases

These are the known trap classes. Cover them in new tests.

1. **Empty/blank inputs.** `False`-y `response`, empty `context`, `tool_calls=[]`,
   blank `premise`/`hypothesis`. Prefer explicit `"skipped"`/`"no context"` issues.
2. **Null injection.** `None` in a response that schema does not allow → flagged as
   "null injection". Respect `_schema_allows_null`.
3. **Forbidden/web sources.** `allow_web` gates source detection; a response citing
   `Wikipedia` or an ambiguous URL must be detected regardless of context.
4. **Cross-dimension embeddings.** Validator must raise / skip cleanly on
   mismatched vector lengths, not silently return.
5. **Rounding.** Scores must stay in `[0.0, 1.0]` after clamping; use `max(0.0,
   min(1.0, ...))` in all verifier/clamp paths.
6. **Async/sync mismatch.** A sync-only verifier used with the async path: the
   async path must detect awaitables and fall back cleanly. Don't `await` a sync
   return value; run the sequence. Keep async attributes aligned with the sync ones.
7. **Unknown tool name vs typo.** A near-miss name must get a `did you mean`
   suggestion; a totally different name must not.
8. **Threshold boundaries.** similarity at exactly `0.7` (`supported`) and `0.4`
   (`weak`, the `weak_threshold`) must land in the right buckets; a `0.39` input
   must be `unsupported`. Test the boundary, not just the middle.
9. **Strict vs non-strict.** A new feature that worsens confidence may flip a
   `balanced` (low risk) into `high` (raises). Recheck `strict` after any scoring change.

---

## Efficiency

- Keep the happy path **dependency-free**: the NLI/embedding code lives behind
  optional extras (`hallx[nli]`) with *lazy imports* inside functions, not module top-level.
- Fuzzy fallback (rapidfuzz) is O(n²) on long docs; for big context, prefer
  embeddings or a precomputed `context_embeddings`, and cache vectors.
- Cache adapter/model instances on the verifier (see `LocalNLIChecker._model`).
  Don't reload models per-`verify` call.
- Avoid recomputing the same evidence loop in both sync and async — factor the
  shared scoring, keep only the I/O differences (`_best_evidence` vs
  `_best_evidence_async` split the work).
- Batch LLM judge calls when possible; a `GroundingJudge` per claim is N
  round-trips. For large responses, prefer a single judge pass.
- Never store redundant copies of sentence spans; pass `(text, start, end)` tuples.

---

## Knowledge transfer

- Keep the `.skills` docs current with each behavior change. `skills.md` maps
  modules to responsibilities; `conventional.md` is the binding style.
- Prefer exporting the symbol you need from `hallx/__init__.py` (everything public
  must be importable from `hallx`), and keep `__all__` alphabetical.
- Type things: every public dataclass/protocol lives in `hallx/types.py` — a new
  check needing a result shape must add a dataclass there first.
- When changing scoring, re-baseline against the `risk_level` thresholds — do not
  move them globally without a reason and a test.
- When renaming a symbol, `git grep` the README, docs, `.skills`, samples, and
  every test.

---

## Before you ship

1. Run `python -m pytest -q` — all must pass (or document a pre-existing flake).
2. Run `python -m py_compile` on changed files.
3. Run any `samples/*.py` that touch changed APIs (they run from repo root).
4. Update `README.md`, `.skills/*.md`, and `CHANGELOG.md` if user-visible.
5. No secrets, no credentials in code or docs.
6. Commit only when the human asks; never stage without being asked.
7. Never create files outside the repo (todo caches etc.).

---

## Finished state checklist

- [ ] New API exported in `hallx/__init__.py` (and `types.py` if needed)
- [ ] Typed return values; no raw dict escapes
- [ ] Test file mirrors module (`tests/test_<module>.py`)
- [ ] Test covers at least 1 empty/blank, 1 boundary, 1 sync and 1 async path
- [ ] `strict=True` path does not break (raises documented)
- [ ] Optional extras lazily imported, core stays lean
- [ ] Samples run from repo root (`PYTHONPATH=. python samples/...`)
- [ ] `pytest -q` green, no new warnings beyond known `asyncio_mode` notice