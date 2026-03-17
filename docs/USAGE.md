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

## UQLM naming compatibility

```python
from hallx import UQLM
# or: from uqlm import UQLM

checker = UQLM(strict=True)
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

## Middleware pattern

Use `result.recommendation` as execution metadata:

- `action`: `proceed` or `retry`
- `suggested_temperature`: lower values when risk is elevated
- `suggestions`: policy hints for the next call

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
