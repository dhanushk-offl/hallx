# hallx

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)
[![Python](https://img.shields.io/pypi/pyversions/hallx.svg)](https://pypi.org/project/hallx/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Lightweight hallucination-risk scoring for production LLM pipelines.

## Overview

| Area | What Hallx Provides |
|---|---|
| Risk output | `confidence` (`0.0` to `1.0`) and `risk_level` (`high`, `medium`, `low`) |
| Diagnostics | `issues` list for tracing weak signals and policy failures |
| Actionability | `recommendation` payload (`action`, `suggested_temperature`, `suggestions`) |
| API modes | Sync and async checks |
| Integrations | Adapter-based and callable-based workflows |
| Operations | Feedback storage and calibration reporting |

Hallx is designed as a guardrail layer before downstream actions such as API responses, automation steps, and database writes.

## Installation

```bash
pip install hallx
```

Development install:

```bash
pip install -e .[dev]
```

## Quick Start

```python
from hallx import Hallx

checker = Hallx(profile="balanced", strict=False)
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
print(result.issues)
print(result.recommendation)
```

## Scoring Model

Hallx uses heuristic risk scoring across three signals:

| Signal | Description |
|---|---|
| `schema` | JSON schema validity and null-injection checks |
| `consistency` | Stability across repeated generations |
| `grounding` | Claim-context alignment and source-integrity checks |

Confidence formula:

```text
confidence = clamp(
  schema_score * w_schema +
  consistency_score * w_consistency +
  grounding_score * w_grounding,
  0.0, 1.0
)
```

Default (`balanced`) weights:

| Weight | Value |
|---|---|
| `w_schema` | `0.34` |
| `w_consistency` | `0.33` |
| `w_grounding` | `0.33` |

Risk mapping:

| Confidence range | Risk |
|---|---|
| `< 0.40` | `high` |
| `< 0.75` | `medium` |
| `>= 0.75` | `low` |

Note: skipped checks are penalized by default to avoid over-trusting partial analysis.

## Safety Profiles

| Profile | Goal | Default `consistency_runs` | Skip penalty |
|---|---|---:|---:|
| `fast` | lower latency | 2 | 0.15 |
| `balanced` | general-purpose | 3 | 0.25 |
| `strict` | stronger scrutiny | 4 | 0.40 |

```python
from hallx import Hallx

checker = Hallx(profile="strict")
```

You can override `weights`, `consistency_runs`, and `skip_penalty` as needed.

## Workflow

![Hallx working flow](docs/images/hallx-working-flow.svg)

1. Collect prompt, optional context, optional schema.
2. Generate a model response through an adapter or callable.
3. Run `schema`, `consistency`, and `grounding` checks.
4. Aggregate scores into `confidence` and `risk_level`.
5. Apply policy (`proceed` or `retry`) using recommendation metadata.
6. Optionally record reviewed outcomes for calibration.

## Adapters

| Provider adapter |
|---|
| OpenAI |
| Anthropic |
| Gemini |
| OpenRouter |
| Perplexity |
| Grok |
| HuggingFace |
| Ollama |

## Samples

| Sample | Purpose |
|---|---|
| `samples/basic_sync.py` | minimal sync workflow |
| `samples/async_openai_adapter.py` | async provider check with context |
| `samples/async_openai_adapter_no_context.py` | no-context behavior and weighting example |
| `samples/retry_strategy.py` | recommendation-driven retry policy |
| `samples/strict_mode.py` | strict blocking behavior |
| `samples/feedback_calibration.py` | local feedback storage and calibration report |
| `samples/async_openai_feedback_calibration.py` | async generation + feedback in one loop |

## Feedback Storage and Calibration

```python
from hallx import Hallx

checker = Hallx(feedback_db_path="/var/lib/myapp/hallx-feedback.sqlite3")

result = checker.check(prompt="p", response="r", context=["c"])
checker.record_outcome(
    result=result,
    label="hallucinated",  # aliases: safe -> correct, unsafe -> hallucinated
    metadata={"reviewer": "qa-team"},
    prompt="p",
    response_excerpt="r",
)

report = checker.calibration_report(window_days=30)
print(report["suggested_threshold"], report["threshold_metrics"])
```

Default DB path resolution:

| Environment | Default path |
|---|---|
| Env override | `HALLX_FEEDBACK_DB` |
| Windows | `%LOCALAPPDATA%\\hallx\\feedback.sqlite3` (fallback `%APPDATA%`) |
| macOS | `~/Library/Application Support/hallx/feedback.sqlite3` |
| Linux/servers | `$XDG_DATA_HOME/hallx/feedback.sqlite3` or `~/.local/share/hallx/feedback.sqlite3` |

## Production Notes

| Recommendation | Why |
|---|---|
| Enable strict mode on sensitive paths | block high-risk responses before side effects |
| Log `confidence`, `risk_level`, `issues` | support auditing and threshold tuning |
| Use calibration report regularly | adjust thresholds with real reviewed outcomes |
| Keep context quality high | grounding quality depends on evidence quality |

## Known Limitations

- Hallx is heuristic and does not provide formal factual guarantees.
- High confidence can still be wrong if context is missing, stale, or incorrect.
- Similarity-based checks can miss nuanced semantic contradictions.
- High-stakes domains should combine Hallx with domain validators and human review.

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Production Notes](docs/PRODUCTION.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)
