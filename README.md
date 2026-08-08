<h1 align="center">hallx</h1>

<p align="center">
  <img src="https://res.cloudinary.com/dwir71gi2/image/upload/v1774898674/Untitled_2_b5xwxj.png" alt="hallx logo" style="width:50%; max-width:720px; height:auto;">
</p>

<p align="center">
  Lightweight hallucination-risk scoring for production LLM pipelines
</p>

<p align="center">
  <a href="https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg"></a>
  <a href="https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml"><img alt="Release" src="https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx"><img alt="OpenSSF Scorecard" src="https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge"></a>
  <a href="https://pypi.org/project/hallx/"><img alt="PyPI" src="https://img.shields.io/pypi/v/hallx.svg"></a>
  <a href="https://pypistats.org/packages/hallx"><img alt="Downloads / month" src="https://img.shields.io/badge/dynamic/json?label=downloads%2Fmonth&query=data.last_month&url=https%3A%2F%2Fpypistats.org%2Fapi%2Fpackages%2Fhallx%2Frecent&color=0f766e"></a>
  <a href="https://pypi.org/project/hallx/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/hallx.svg"></a>
  <a href="https://github.com/dhanushk-offl/hallx/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
</p>

## What Is Hallx

Hallx is a practical guardrail layer that evaluates LLM responses before they are trusted in downstream systems.

It scores responses using:
- `schema` validity
- `consistency` across repeated generations
- `grounding` against provided context

It returns:
- `confidence`
- `risk_level`
- `issues`
- `recommendation`

For agentic and retrieval flows, hallx adds three deeper guards:

- **Claim-level grounding** — splits the response into individual claims and verifies each one against its best evidence snippet, surfacing exactly which sentences are *supported*, *weak*, or *unsupported*.
- **Pluggable verifiers** — swap in local NLI (`LocalNLIChecker`, `hallx[nli]`) or an **LLM-as-judge** (`GroundingJudge`) to score claim–evidence entailment.
- **Tool-call validation** — catch hallucinated tool names and malformed arguments in agentic LLM output before a handler executes them.

## Quick Start

```bash
pip install hallx
```

```python
from hallx import Hallx

checker = Hallx(profile="balanced")
result = checker.check(prompt="p", response="r", context=["c"])
print(result.confidence, result.risk_level, result.recommendation)
```

## Claim-Level Grounding

Detect *which sentence in the response* has evidence, and which is invented:

```python
from hallx.attribution import check_claim_grounding

response = "The Eiffel Tower is in Paris. The Eiffel Tower is also in Berlin."
context = ["The Eiffel Tower is located in Paris, France."]

result = check_claim_grounding(response, context)

for claim in result.claims:
    if claim.status != "filtered":
        print(f"[{claim.status}] {claim.text}")
```

```text
[supported] The Eiffel Tower is in Paris.
[unsupported] The Eiffel Tower is also in Berlin.
```

The result exposes `score`, `supported_count`, `weak_count`, `unsupported_count`, and per-claim `similarity`, `evidence_index`, and `evidence_snippet`. Use `hallx.extract_claims` alone to get the typed `Claim` spans.

### Semantically grounded with a verifier

By default clashes are scored with fuzzy text similarity — fast and dependency-free. For real NLI, pass a `FaithfulnessVerifier`:

```python
from hallx.faithfulness import LocalNLIChecker   # needs: pip install 'hallx[nli]'

verifier = LocalNLIChecker()
result = check_claim_grounding(response, context, verifier=verifier)
```

Or use any hallx LLM adapter as an **LLM-as-judge** (no extra dependency):

```python
from hallx import OpenAIAdapter
from hallx.judge import GroundingJudge

judge = GroundingJudge(llm_adapter=OpenAIAdapter("gpt-4o-mini", api_key="..."))
result = check_claim_grounding(response, context, verifier=judge)
```

### Claim checks inside the main `check`

Enable claim-level evidence on every `Hallx.check` call and the verdict lands on `result.evidence`:

```python
from hallx import Hallx
from hallx.judge import GroundingJudge

checker = Hallx()
judge = GroundingJudge(llm_adapter=OpenAIAdapter("gpt-4o-mini", api_key="..."))

result = checker.check(
    prompt="Summarize the refund policy",
    response="Refunds are allowed within 30 days.",
    context=["Refunds are allowed within 30 days of purchase."],
    claims=True,
    verifier=judge,
)

print(result.claim_grounding_score)      # mean claim grounding
print(result.claims_supported)           # count of supported claims
print(result.unsupported_claims)         # the hallucinated bits, if any
```

Both `check` and `check_async` accept `claims=True` and `verifier=...`. Embedding-backed scoring works too: pass `embedding_callable` and optionally `context_embeddings`.

## Tool-Call Validation

Guard agentic pipelines against hallucinated tool calls before execution:

```python
from hallx import Hallx

tools = {
    "get_weather": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
        "additionalProperties": False,
    },
    "send_email": {"parameters": {"type": "object", "properties": {"to": {"type": "string"}}, "required": ["to"]}},
}

checker = Hallx()
agent_output = [
    {"function": {"name": "get_weather", "arguments": '{"city": "Paris"}'}},
    {"name": "rm -rf", "arguments": "{}"},          # hallucinated tool name
]

result = checker.check_tool_call(agent_output, tools)
print(result.score)                                  # 0.25
print(result.verdicts)                               # ok / unknown_tool
if result.recommendation["action"] == "block":
    print("Regenerate before invoking any tool.")
```

Accepts raw `(name, arguments)` pairs, dicts, OpenAI-style `{function: ...}` payloads, and typed `ToolCall` instances. The standalone `check_tool_call` / `score_tool_calls` helpers are exported too. Verdict statuses: `ok`, `invalid_arguments`, `malformed`, `unknown_tool`.

## Workflow

<p align="center">
  <img src="https://res.cloudinary.com/dwir71gi2/image/upload/v1774899848/hallx-working-flow_xh213f.svg" alt="Hallx workflow" width="100%">
</p>

## Essential Links

### Languages
- [English](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.en.md)
- [Tamil](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.ta.md)
- [Malayalam](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.ml.md)
- [Hindi](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.hi.md)
- [Kannada](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.kn.md)
- [German](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.de.md)
- [Japanese](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.ja.md)
- [Chinese](https://github.com/dhanushk-offl/hallx/blob/master/docs/README.zh.md)

### Community
- [Contributing](https://github.com/dhanushk-offl/hallx/blob/master/CONTRIBUTING.md)
- [GitHub Sponsors](https://github.com/sponsors/dhanushk-offl)
- [Buy Me a Coffee](https://buymeacoffee.com/itzmedhanu)
- [Monthly Downloads (PyPIStats)](https://pypistats.org/packages/hallx)
