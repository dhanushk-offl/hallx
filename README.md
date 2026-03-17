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

It also supports UQLM-style naming via `UQLM` and `uqlm`.

## How Hallx Works

Hallx combines three checks into a single confidence score:

- `schema`: is the output structurally valid for your expected JSON schema?
- `consistency`: does the model give stable answers across repeated runs?
- `grounding`: do the response claims align with your provided context?

Final confidence is mapped to risk:
- `< 0.40` -> `high`
- `< 0.75` -> `medium`
- `>= 0.75` -> `low`

![Hallx working flow](docs/images/hallx-working-flow.svg)

## Why Hallx

LLM failures in production are often fluent but unsafe:
- unsupported claims against RAG context
- unstable outputs across retries
- broken structured JSON
- fabricated source/citation patterns

Hallx makes these failure modes explicit so you can gate, retry, or escalate.

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

What these samples demonstrate:
- low-risk baseline question
- hallucination-prone future claim (`Nobel Prize 2027`)
- hallucination-prone medical/citation-style claim

Notes:
- without `context`, Hallx skips grounding and reports it in `issues`
- high-risk outcomes are probabilistic and model-dependent; if needed, increase `temperature` and `consistency_runs` to expose instability
- in the no-context sample, weights are tuned to focus on schema + consistency:
  `{"schema": 0.5, "consistency": 0.5, "grounding": 0.0}`

UQLM-style import:

```python
from hallx import UQLM
# or: from uqlm import UQLM
```

## Key Features

- Deterministic consistency scoring across repeated generations
- Grounding checks against provided context
- JSON Schema validation with actionable issue messages
- Weighted confidence aggregation
- Strict mode (`HallxHighRiskError`) for hard safety gates
- Sync and async APIs
- Multi-provider adapters (OpenAI, Anthropic, Gemini, OpenRouter, Perplexity, Grok, HuggingFace)

## Production Usage

- Enable strict mode for high-risk blocking paths.
- Use `result.recommendation` to drive retry policy.
- Log `confidence`, `risk_level`, and `issues` for observability.

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
