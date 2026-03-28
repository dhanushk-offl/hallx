# Usage Guide

## Basic flow

```python
from hallx import Hallx

checker = Hallx()
result = checker.check(
    prompt="Summarize the policy",
    response={"summary": "Refunds are allowed in 30 days."},
    context=["Refunds are allowed within 30 days of purchase."],
)

print(result.confidence)
print(result.risk_level)
print(result.recommendation)
```

## Strict mode

```python
from hallx import Hallx, HallxHighRiskError

checker = Hallx(strict=True)

try:
    checker.check(prompt="p", response="r")
except HallxHighRiskError:
    # Block response and trigger fallback policy.
    pass
```

## Safety profiles

```python
from hallx import Hallx

fast_checker = Hallx(profile="fast")
balanced_checker = Hallx(profile="balanced")  # default
strict_checker = Hallx(profile="strict")
```

Profile defaults:
- `fast`: `consistency_runs=2`, lower skip penalty
- `balanced`: `consistency_runs=3`
- `strict`: `consistency_runs=4`, higher grounding weight and skip penalty

Skip behavior:
- If consistency or grounding is skipped, Hallx applies a score penalty by default.
- You can override with `skip_penalty=...` when constructing `Hallx`.

## Middleware pattern

Use `result.recommendation` as execution metadata:

- `action`: `proceed` or `retry`
- `suggested_temperature`: lower values when risk is elevated
- `suggestions`: policy hints for the next call

## Feedback storage (SQLite) and calibration

```python
from hallx import Hallx

checker = Hallx(feedback_db_path="C:/data/hallx-feedback.sqlite3")

result = checker.check(prompt="p", response="r", context=["c"])
checker.record_outcome(
    result=result,
    label="correct",  # aliases: safe -> correct, unsafe -> hallucinated
    metadata={"reviewer": "ops"},
)

report = checker.calibration_report(window_days=30)
print(report["hallucination_rate"])
print(report["suggested_threshold"])
```

If `feedback_db_path` is omitted, Hallx uses:
- `HALLX_FEEDBACK_DB` env var when set
- otherwise an OS-adaptive default:
- Windows: `%LOCALAPPDATA%\\hallx\\feedback.sqlite3` (fallback `%APPDATA%`)
- macOS: `~/Library/Application Support/hallx/feedback.sqlite3`
- Linux/servers: `$XDG_DATA_HOME/hallx/feedback.sqlite3` or `~/.local/share/hallx/feedback.sqlite3`

Walkthrough:
1. Run `checker.check(...)` for each model output.
2. After human review, call `checker.record_outcome(result, label, ...)`.
3. Collect outcomes over time in the same DB file.
4. Run `checker.calibration_report(...)` to evaluate your current policy.
5. Update your runtime threshold or retry policy using the report.

Ready-to-run demo:

```bash
python samples/feedback_calibration.py
```

Async + feedback in the same loop:

```bash
python samples/async_openai_feedback_calibration.py
```

## Async OpenAI adapter examples

`samples/async_openai_adapter.py`:
- runs with grounding `context`
- includes baseline + hallucination-prone prompts
- prints `confidence`, `risk_level`, `scores`, and `issues`

`samples/async_openai_adapter_no_context.py`:
- runs without `context`
- demonstrates `"grounding check skipped: no context provided"`
- uses weights `{"schema": 0.5, "consistency": 0.5, "grounding": 0.0}` to focus non-grounding signals

Run:

```bash
python samples/async_openai_adapter.py
python samples/async_openai_adapter_no_context.py
```

Set key first:

```bash
export OPENAI_API_KEY="your_key_here"
```
