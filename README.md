# hallx

[![Python Tests](https://github.com/dhanushkandhan/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushkandhan/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushkandhan/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushkandhan/hallx/actions/workflows/release.yml)
[![PyPI version](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)
[![Python versions](https://img.shields.io/pypi/pyversions/hallx.svg)](https://pypi.org/project/hallx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Lightweight, production-focused hallucination risk detection for LLM outputs.

`hallx` gives you:
- confidence score (`0.0` to `1.0`)
- risk level (`high`, `medium`, `low`)
- issue list you can inspect/log
- retry recommendation payload for middleware automation

It supports sync + async checking with adapter- or callable-based workflows.

## How Hallx Works

Hallx combines three checks into a single confidence score:

- `schema`: is the output structurally valid for your expected JSON schema?
- `consistency`: does the model give stable answers across repeated runs?
- `grounding`: do the response claims align with your provided context?

Final confidence is mapped to risk:
- `< 0.40` -> `high`
- `< 0.75` -> `medium`
- `>= 0.75` -> `low`

### Heuristic Scoring Model

Hallx uses **heuristic risk scoring**. That means it estimates hallucination risk from practical signals, not from a formal truth-proof engine.

Signals:
- `schema`: JSON/schema correctness
- `consistency`: stability across repeated generations
- `grounding`: alignment of response claims with provided context

Confidence formula:

```text
confidence = clamp(
  schema_score * w_schema +
  consistency_score * w_consistency +
  grounding_score * w_grounding,
  0.0, 1.0
)
```

Default weights:
- `w_schema = 0.34`
- `w_consistency = 0.33`
- `w_grounding = 0.33`

Important:
- This is a risk estimator, not guaranteed factual verification.
- In high-stakes use cases, pair Hallx with stronger evidence verification and human review.
- By default, skipped checks are penalized in confidence scoring to avoid over-trusting incomplete analysis.

![Hallx working flow](docs/images/hallx-working-flow.svg)

### Flow Walkthrough

1. Input: send prompt plus optional context and JSON schema.
2. Generation: run model through an adapter or callable.
3. Analysis: Hallx evaluates schema, consistency, and grounding.
4. Scoring: Hallx computes confidence and risk level.
5. Action: application uses recommendation (`proceed` or `retry`).
6. Review: human or QA labels the outcome (`correct` or `hallucinated`).
7. Storage: outcome is written to SQLite on device/server.
8. Calibration: report suggests safer threshold from real data.

## Why Hallx

LLM failures in production are often fluent but unsafe:
- unsupported claims against RAG context
- unstable outputs across retries
- broken structured JSON
- fabricated source/citation patterns

Hallx makes these failure modes explicit so you can gate, retry, or escalate.

## Who Should Use Hallx

Use Hallx if you are building:
- LLM apps that return JSON or machine-consumed responses
- RAG/chat systems where grounding to trusted context matters
- Production pipelines that need retry/block policy based on risk
- QA/ops workflows that want feedback-driven calibration over time

Hallx is especially useful as a **guardrail layer** before downstream actions (DB writes, automation, user-visible answers).

Hallx is not a replacement for:
- full factual verification systems
- domain-specific validators (medical/legal/financial correctness checks)

## Installation

```bash
pip install hallx
```

Dev install:

```bash
pip install -e .[dev]
```

## Quick Start

```python
from hallx import Hallx

checker = Hallx(strict=False)

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
print(result.issues)
print(result.recommendation)
```

### Safety Profiles

Hallx includes built-in profile presets:
- `fast`: lower latency (`consistency_runs=2`), smaller skip penalty
- `balanced` (default): general purpose (`consistency_runs=3`)
- `strict`: stronger scrutiny (`consistency_runs=4`), higher grounding weight and skip penalty

```python
from hallx import Hallx

checker = Hallx(profile="strict")
```

You can still override:
- `weights=...` for custom weighting
- `consistency_runs=...` per check call
- `skip_penalty=...` at checker construction

## Async OpenAI Samples (With and Without Context)

Set your key:

```bash
export OPENAI_API_KEY="your_key_here"
```

Run with grounding context:

```bash
python samples/async_openai_adapter.py
```

Run without context:

```bash
python samples/async_openai_adapter_no_context.py
```

Feedback loop sample:

```bash
python samples/feedback_calibration.py
```

Async OpenAI + feedback recording in one loop:

```bash
python samples/async_openai_feedback_calibration.py
```

What these samples demonstrate:
- low-risk baseline question
- hallucination-prone future claim (`Nobel Prize 2027`)
- hallucination-prone medical/citation-style claim

Notes:
- without `context`, Hallx skips grounding and reports it in `issues`
- high-risk outcomes are probabilistic and model-dependent; if needed, increase `temperature` and `consistency_runs` to expose instability
- in the no-context sample, weights are tuned to focus on schema + consistency:
  `{"schema": 0.5, "consistency": 0.5, "grounding": 0.0}`

## Key Features

- Deterministic consistency scoring across repeated generations
- Grounding checks against provided context
- JSON Schema validation with actionable issue messages
- Weighted confidence aggregation
- Skip-aware confidence penalty when checks are skipped
- Built-in safety profiles (`fast`, `balanced`, `strict`)
- Strict mode (`HallxHighRiskError`) for hard safety gates
- SQLite-backed feedback storage for human-reviewed outcomes
- Calibration reporting to tune confidence thresholds from real outcomes
- Sync and async APIs
- Multi-provider adapters (OpenAI, Anthropic, Gemini, OpenRouter, Perplexity, Grok, HuggingFace, Ollama)

## Known Limitations

- Hallx is heuristic, not a formal fact-verification engine.
- Strong confidence can still be wrong when source context itself is incomplete or incorrect.
- Fuzzy/embedding similarity can miss nuanced contradictions in complex domains.
- For high-stakes domains, use Hallx as a guardrail layer alongside domain validators and human review.

## Production Usage

- Enable strict mode for high-risk blocking paths.
- Use `result.recommendation` to drive retry policy.
- Log `confidence`, `risk_level`, and `issues` for observability.
- Store review feedback in SQLite (device or server path) to calibrate thresholds over time.

### Feedback Storage and Calibration

```python
from hallx import Hallx

checker = Hallx(feedback_db_path="/var/lib/myapp/hallx-feedback.sqlite3")
# Or set env once:
# export HALLX_FEEDBACK_DB="/var/lib/myapp/hallx-feedback.sqlite3"

result = checker.check(prompt="p", response="r", context=["c"])
checker.record_outcome(
    result=result,
    label="hallucinated",   # also accepts safe/unsafe aliases
    metadata={"reviewer": "qa-team"},
    prompt="p",
    response_excerpt="r",
)

report = checker.calibration_report(window_days=30)
print(report["suggested_threshold"], report["threshold_metrics"])
```

Behavior details:
- Default DB path resolution:
- `HALLX_FEEDBACK_DB` env var first
- else OS-adaptive path:
- Windows: `%LOCALAPPDATA%\\hallx\\feedback.sqlite3` (fallback `%APPDATA%`)
- macOS: `~/Library/Application Support/hallx/feedback.sqlite3`
- Linux/servers: `$XDG_DATA_HOME/hallx/feedback.sqlite3` or `~/.local/share/hallx/feedback.sqlite3`
- Preferred labels: `correct` or `hallucinated` (aliases `safe` and `unsafe` are accepted)
- Report output includes totals, hallucination rate, risk-level breakdown, and threshold suggestion

More:
- [Usage Guide](docs/USAGE.md)
- [Production Notes](docs/PRODUCTION.md)

## Development

Run tests:

```bash
python -m pytest
```

Run packaging checks:

```bash
python -m build
python -m twine check dist/*
```

## CI and Release

- Push to `main`/`master`: runs test workflow.
- Push tag `v*` (example: `v0.1.1`): runs release workflow and creates GitHub Release with package artifacts.

## Community

- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)
