# Usage Guide

This guide focuses on practical integration patterns for production codebases.

## Contents

- Core sync integration
- Async integration
- Safety profiles and tuning
- Strict gating pattern
- Retry middleware pattern
- Feedback storage and calibration
- Adapter usage
- Sample scripts

## Core Sync Integration

```python
from hallx import Hallx

checker = Hallx(profile="balanced")

result = checker.check(
    prompt="Summarize refund policy",
    response={"summary": "Refunds are allowed within 30 days."},
    context=["Refunds are allowed within 30 days of purchase."],
    schema={
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
        "additionalProperties": False,
    },
)

print(result.confidence, result.risk_level)
print(result.scores)
print(result.coverage)
print(result.issues)
print(result.recommendation)
```

When to use sync mode:
- request-scoped checks in API handlers
- batch pipelines that already run synchronously

## Async Integration

```python
result = await checker.check_async(
    prompt=prompt,
    response=response,
    context=context_docs,
    llm_adapter=adapter,
    consistency_runs=4,
)
```

When to use async mode:
- async web services
- high-throughput workers
- provider adapters with async generation

## Safety Profiles and Tuning

```python
from hallx import Hallx

fast_checker = Hallx(profile="fast")
balanced_checker = Hallx(profile="balanced")  # default
strict_checker = Hallx(profile="strict")
```

Profile defaults:

| Profile | `consistency_runs` | Skip penalty |
|---|---:|---:|
| `fast` | 2 | 0.15 |
| `balanced` | 3 | 0.25 |
| `strict` | 4 | 0.40 |

Override options:
- `weights={...}` for custom score weighting
- `consistency_runs=...` per call
- `skip_penalty=...` at checker construction
- `required_checks={"grounding", "schema"}` to require individual checks

## Evaluation Coverage

`result.coverage` maps `schema`, `consistency`, and `grounding` to a
`CheckCoverage` object with `status` (`evaluated` or `skipped`) and a `reason`
when skipped. Invalid output still counts as evaluated if the check ran.

Hallx requires at least one of grounding or consistency to run. If neither runs,
or a check listed in `required_checks` is skipped, the risk level is
`insufficient_evidence` and the recommended action is `review`. A score that
already indicates high risk retains the `high` verdict. `strict=True` rejects
both high risk and insufficient evidence; `assert_safe` also rejects
insufficient evidence, regardless of its confidence threshold.

This is a behavior change: code that previously accepted a low-risk result when
checks were skipped should handle the new risk level and `review` action. The
confidence score and skip penalties are unchanged; confidence is a heuristic,
not a calibrated probability of correctness. A completed check does not prove
that an answer is correct.

## Strict Gating Pattern

```python
from hallx import Hallx, HallxHighRiskError

checker = Hallx(strict=True, profile="strict")

try:
    result = checker.check(prompt="p", response="r", context=["c"])
except HallxHighRiskError:
    # block output and run fallback policy
    ...
```

Use this on:
- machine-executed outputs
- sensitive business workflows
- customer-facing high-risk responses

## Retry Middleware Pattern

Use `result.recommendation` as runtime metadata:

- `action`: `proceed`, `retry`, or `review` (insufficient evidence)
- `suggested_temperature`
- `suggestions`

Example flow:
1. Call model once.
2. Score response with Hallx.
3. If `action == "retry"`, rerun with lower temperature and better context.
4. Stop after policy-defined retry budget.

## Feedback Storage and Calibration

```python
from hallx import Hallx

checker = Hallx(feedback_db_path="/var/lib/myapp/hallx-feedback.sqlite3")
result = checker.check(prompt="p", response="r", context=["c"])

checker.record_outcome(
    result=result,
    label="correct",  # aliases: safe -> correct, unsafe -> hallucinated
    metadata={"reviewer": "ops"},
    prompt="p",
    response_excerpt="r",
)

report = checker.calibration_report(window_days=30)
print(report["hallucination_rate"])
print(report["suggested_threshold"])
```

Storage path resolution:

| Environment | Path |
|---|---|
| Env override | `HALLX_FEEDBACK_DB` |
| Windows | `%LOCALAPPDATA%\\hallx\\feedback.sqlite3` (fallback `%APPDATA%`) |
| macOS | `~/Library/Application Support/hallx/feedback.sqlite3` |
| Linux/servers | `$XDG_DATA_HOME/hallx/feedback.sqlite3` or `~/.local/share/hallx/feedback.sqlite3` |

## Adapter Usage

Available adapters:
- OpenAI
- Anthropic
- Gemini
- OpenRouter
- Perplexity
- Grok
- HuggingFace
- Ollama

Choose adapters when:
- you want standard provider payload handling
- you need consistent sync/async integration across providers

Use callables when:
- your model stack is custom
- you want full control over request/response flow

## Sample Scripts

| Script | Purpose |
|---|---|
| `samples/basic_sync.py` | minimal sync usage |
| `samples/retry_strategy.py` | recommendation-driven retry loop |
| `samples/strict_mode.py` | strict blocking behavior |
| `samples/async_openai_adapter.py` | async check with grounding context |
| `samples/async_openai_adapter_no_context.py` | no-context behavior |
| `samples/feedback_calibration.py` | reviewed feedback + calibration |
| `samples/async_openai_feedback_calibration.py` | async + feedback in one loop |

Run examples:

```bash
python samples/basic_sync.py
python samples/retry_strategy.py
python samples/feedback_calibration.py
```
