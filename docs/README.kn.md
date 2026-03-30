# hallx (ಕನ್ನಡ)

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` என்பது LLM output-ಗಳಿಗೆ lightweight risk-scoring guardrail library.  
Production ನಲ್ಲಿ output ನಂಬುವ ಮುನ್ನ ಒಂದು practical ಪ್ರಶ್ನೆಗೆ ಉತ್ತರ ಕೊಡುತ್ತದೆ:

`ಈ output ಎಷ್ಟು risk ಹೊಂದಿದೆ?`

## Hallx ಯಾಕೆ

Production ನಲ್ಲಿ LLM failures subtle ಆಗಿರುತ್ತವೆ:

- output fluent ಆಗಿರುತ್ತದೆ, ಆದರೆ evidence support ಇಲ್ಲ
- JSON ಸರಿಯಂತೆ ಕಾಣುತ್ತದೆ, strict parser ನಲ್ಲಿ fail ಆಗುತ್ತದೆ
- same prompt ಗೆ repeated generation stable ಇರದೇ ಇರಬಹುದು

Hallx risk ಅನ್ನು operational ರೀತಿಯಲ್ಲಿ measure ಮಾಡಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ:

- response score ಮಾಡುತ್ತದೆ
- issues ತೋರಿಸುತ್ತದೆ
- proceed/retry policy ನಿರ್ಧರಿಸಲು ನೆರವಾಗುತ್ತದೆ
- feedback ಆಧರಿಸಿ thresholds tune ಮಾಡಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ

## Hallx ಏನು ಕೊಡುತ್ತದೆ

| ಸಾಮರ್ಥ್ಯ | Output |
|---|---|
| Risk scoring | `confidence` (`0.0` ರಿಂದ `1.0`) |
| Risk label | `risk_level` (`high`, `medium`, `low`) |
| Diagnostics | `issues` list |
| Policy hints | `recommendation` payload |
| Governance | feedback storage + calibration report |

## ಯಾರಿಗೆ ಉಪಯೋಗ

- RAG/chat features build ಮಾಡುವ ತಂಡಗಳಿಗೆ
- machine-consumed JSON ನೀಡುವ backend workflows ಗೆ
- retry/block policy ರೂಪಿಸುವ ops/QA ತಂಡಗಳಿಗೆ
- LLM output ಮೂಲಕ automation trigger ಮಾಡುವ systems ಗೆ

ಗಮನಿಸಿ: medical/legal/financial high-stakes domains ನಲ್ಲಿ domain validators + human review ಅಗತ್ಯ.

## Scoring Model

Hallx ಮೂರು heuristic signals ಆಧರಿಸಿ score ಲೆಕ್ಕ ಹಾಕುತ್ತದೆ:

- `schema`: structured output validity
- `consistency`: repeated generation stability
- `grounding`: claim-context alignment

```text
confidence = clamp(
  schema_score * w_schema +
  consistency_score * w_consistency +
  grounding_score * w_grounding,
  0.0, 1.0
)
```

Default (`balanced`) weights:
- `w_schema = 0.34`
- `w_consistency = 0.33`
- `w_grounding = 0.33`

Risk mapping:
- `< 0.40` -> `high`
- `< 0.75` -> `medium`
- `>= 0.75` -> `low`

Skipped checks ಗೆ default penalty ಇರುತ್ತದೆ; partial analysis ಮೇಲೆ over-trust ತಪ್ಪಿಸಲು ಇದು ಉಪಯೋಗಿ.

## End-to-End Workflow

![Hallx workflow](images/hallx-working-flow.svg)

1. Prompt + optional context/schema ಪಡೆಯಿರಿ.
2. Adapter/callable ಮೂಲಕ response generate ಮಾಡಿ.
3. `schema`, `consistency`, `grounding` checks ಓಡಿಸಿ.
4. `confidence` ಮತ್ತು `risk_level` ಪಡೆಯಿರಿ.
5. `recommendation` ಆಧರಿಸಿ proceed/retry policy apply ಮಾಡಿ.
6. Reviewed outcomes store ಮಾಡಿ, calibration ಮೂಲಕ threshold tune ಮಾಡಿ.

## Quick Start

```python
from hallx import Hallx

checker = Hallx(profile="balanced")
result = checker.check(
    prompt="Summarize refund policy",
    response={"summary": "Refunds are allowed within 30 days."},
    context=["Refunds are allowed within 30 days of purchase."],
)

print(result.confidence, result.risk_level)
print(result.issues)
print(result.recommendation)
```

## Safety Profiles

| Profile | ಗುರಿ | Default `consistency_runs` | Skip penalty |
|---|---|---:|---:|
| `fast` | ಕಡಿಮೆ latency | 2 | 0.15 |
| `balanced` | ಸಾಮಾನ್ಯ ಬಳಕೆ | 3 | 0.25 |
| `strict` | ಕಠಿಣ risk ನಿಯಂತ್ರಣ | 4 | 0.40 |

## ಮುಂದಿನ ಓದು

- English: [README.en.md](README.en.md)
- தமிழ்: [README.ta.md](README.ta.md)
- മലയാളം: [README.ml.md](README.ml.md)
- Usage: [USAGE.md](USAGE.md)
- Production: [PRODUCTION.md](PRODUCTION.md)
