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
