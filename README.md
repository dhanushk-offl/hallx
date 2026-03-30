<h1 align="center">hallx</h1>

<p align="center">
  <img src="https://res.cloudinary.com/dwir71gi2/image/upload/v1774898674/Untitled_2_b5xwxj.png" alt="hallx logo" style="width:100%; max-width:720px; height:auto;">
</p>

<p align="center">
  Lightweight hallucination-risk scoring for production LLM pipelines
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

## Workflow

<p align="center">
  <img src="docs/images/hallx-working-flow.svg" alt="Hallx workflow" width="100%">
</p>

## Essential Links

### Languages
- [English](docs/README.en.md)
- [Tamil](docs/README.ta.md)
- [Malayalam](docs/README.ml.md)
- [Hindi](docs/README.hi.md)
- [Kannada](docs/README.kn.md)
- [German](docs/README.de.md)
- [Japanese](docs/README.ja.md)
- [Chinese](docs/README.zh.md)

### Community
- [Contributing](CONTRIBUTING.md)
- [GitHub Sponsors](https://github.com/sponsors/dhanushk-offl)
- [Buy Me a Coffee](https://buymeacoffee.com/itzmedhanu)

