# hallx

`hallx` is a lightweight, model-agnostic hallucination risk engine for LLM outputs.

## What is Hallx?

Hallx runs deterministic checks over model output quality and returns a normalized confidence score (`0..1`), a risk level (`high|medium|low`), actionable issues, and an automatic retry recommendation payload for middleware orchestration.

## Why hallucination detection matters

Production LLM systems can fail in ways that look fluent but are unsafe:

- inconsistent answers across retries,
- claims unsupported by retrieved context,
- malformed structured outputs,
- fabricated citations and fake links.

Hallx makes these failure modes explicit so you can gate, retry, or escalate.

## Features

- Deterministic multi-run consistency scoring
- Context grounding checks for RAG responses
- JSON Schema validation (`missing`, `type`, `enum`, `extra keys`, `null injection`)
- Forbidden source detection (fabricated citation / suspicious URL heuristics)
- Weighted confidence scoring engine
- Retry Strategy Engine (`result.recommendation`)
- Strict guard mode (`HallxHighRiskError`)
- Sync + async APIs
- Provider adapters (OpenAI, OpenRouter, Anthropic, Perplexity, HuggingFace, Gemini, Grok)
- Fully typed, pytest-tested, lightweight dependencies

## Installation

```bash
pip install hallx
```

Development install:

```bash
pip install -e .[dev]
```

## Quickstart

```python
import hallx

checker = hallx.Hallx()

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

print(result.confidence)
print(result.risk_level)
print(result.scores)
print(result.issues)
print(result.recommendation)
```

## Retry Strategy Engine

Hallx auto-generates middleware hints:

```python
{
    "action": "retry",
    "suggested_temperature": 0.2,
    "suggestions": [
        "Lower temperature",
        "Increase context",
        "Force JSON mode",
        "Switch model"
    ]
}
```

Suggested actions are derived from score breakdown and detected issues.

## Advanced Usage

### Custom weights

```python
from hallx import Hallx

checker = Hallx(weights={
    "schema": 0.3,
    "consistency": 0.4,
    "grounding": 0.3,
})
```

### OpenAI-style callable

```python
def llm_callable(prompt: str) -> str:
    return "Answer text"

result = checker.check(
    prompt="question",
    response="Answer text",
    llm_callable=llm_callable,
    consistency_runs=3,
)
```

### Adapter usage (OpenAI)

```python
import os
from hallx import Hallx, OpenAIAdapter

adapter = OpenAIAdapter(model="gpt-4.1-mini", api_key=os.environ["OPENAI_API_KEY"])
checker = Hallx()

response = adapter.generate("What is the capital of France?")
result = checker.check(
    prompt="What is the capital of France?",
    response=response,
    context=["The capital of France is Paris."],
    llm_adapter=adapter,
)
```

### Async example

```python
import asyncio
from hallx import Hallx

checker = Hallx()

async def llm_callable(prompt: str) -> str:
    return "Answer text"

async def main() -> None:
    result = await checker.check_async(
        prompt="question",
        response="Answer text",
        llm_callable=llm_callable,
        context=["Reference context text."],
    )
    print(result.confidence, result.risk_level)
    print(result.recommendation)

asyncio.run(main())
```

### Strict mode

```python
from hallx import Hallx, HallxHighRiskError

checker = Hallx(strict=True)

try:
    checker.check(prompt="p", response="r")
except HallxHighRiskError as exc:
    print(f"blocked: {exc}")
```

### Schema-only validation

```python
report = checker.check_json(response={"answer": None}, schema=my_schema)
print(report.score, report.is_valid, report.issues)
```

## Architecture Overview

Minimal modular structure:

```text
hallx/
+-- core.py          # main Hallx class + orchestration
+-- scoring.py       # confidence aggregation + risk mapping
+-- retry.py         # retry strategy recommendation engine
+-- consistency.py   # multi-run variance checks
+-- grounding.py     # context grounding + source heuristics
+-- schema.py        # JSON/schema integrity checks
+-- types.py         # result models + adapter protocol
+-- adapters/
|   +-- base.py
|   +-- openai.py
|   +-- openrouter.py
|   +-- anthropic.py
|   +-- perplexity.py
|   +-- huggingface.py
|   +-- gemini.py
|   +-- grok.py
+-- __init__.py
```

Scoring pipeline:

1. Parse response safely.
2. Validate schema.
3. Measure consistency over N generations.
4. Check grounding against context.
5. Detect suspicious source references.
6. Combine weighted scores to one confidence value.
7. Produce retry recommendation for middleware action.

## Samples

See [`samples/`](samples):

- `basic_sync.py`
- `retry_strategy.py`
- `strict_mode.py`
- `check_json_only.py`
- `custom_embeddings.py`
- `async_openai_adapter.py`
- `providers_matrix.py`

## Running Tests

```bash
pytest
```

## OpenSSF-Oriented Security Notes

- No dynamic code execution (`eval/exec`) in runtime path.
- Provider adapters enforce request timeout and bounded generation parameters.
- API keys are passed via constructor or env vars, never hardcoded.
- JSON-only transport with strict parsing and explicit error handling.
- Full typing + unit tests for deterministic behavior.
- Dependency surface intentionally small (`jsonschema`, `rapidfuzz`).

## Install Size

Hallx is pure-Python with lightweight dependencies and is designed to stay comfortably under ~1MB for package code itself (excluding optional environment wheels).

## Roadmap

- Logprob scoring
- Multi-model consensus
- Embedding provider plugin interface
- Optional web verification flow
