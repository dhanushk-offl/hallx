# hallx (हिंदी)

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` LLM outputs के लिए एक lightweight risk-scoring guardrail library है।  
Production में response पर भरोसा करने से पहले यह practical सवाल हल करता है:

`इस output का जोखिम कितना है?`

## Hallx क्यों

Production में LLM failures अक्सर subtle होते हैं:

- output fluent होता है, लेकिन evidence से supported नहीं होता
- JSON देखने में सही लगता है, पर strict parser में fail हो जाता है
- same prompt पर repeated generations unstable हो सकती हैं

Hallx इस risk को operational तरीके से measure करने में मदद करता है:

- response score करें
- issues identify करें
- proceed/retry policy apply करें
- feedback से thresholds tune करें

## Hallx क्या देता है

| क्षमता | Output |
|---|---|
| Risk scoring | `confidence` (`0.0` से `1.0`) |
| Risk label | `risk_level` (`high`, `medium`, `low`) |
| Diagnostics | `issues` list |
| Policy hints | `recommendation` payload |
| Governance | feedback storage + calibration report |

## किसके लिए उपयोगी

- RAG/chat features ship करने वाली teams
- machine-consumed JSON देने वाले backend systems
- retry/block policy बनाने वाली ops/QA teams
- LLM output से automation trigger करने वाले workflows

नोट: medical/legal/financial जैसे high-stakes domains में domain validators और human review ज़रूरी हैं।

## Scoring Model

Hallx तीन heuristic signals पर score बनाता है:

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

Skipped checks पर default penalty लागू होती है ताकि partial analysis पर over-trust न हो।

## End-to-End Workflow

![Hallx workflow](images/hallx-working-flow.svg)

1. Prompt + optional context/schema लें।
2. Adapter/callable से response generate करें।
3. `schema`, `consistency`, `grounding` checks चलाएँ।
4. `confidence` और `risk_level` प्राप्त करें।
5. `recommendation` के आधार पर proceed/retry policy लागू करें।
6. Reviewed outcomes store करें और calibration से threshold tune करें।

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

| Profile | लक्ष्य | Default `consistency_runs` | Skip penalty |
|---|---|---:|---:|
| `fast` | कम latency | 2 | 0.15 |
| `balanced` | सामान्य उपयोग | 3 | 0.25 |
| `strict` | कड़ा risk control | 4 | 0.40 |

## आगे पढ़ें

- English: [README.en.md](README.en.md)
- தமிழ்: [README.ta.md](README.ta.md)
- മലയാളം: [README.ml.md](README.ml.md)
- Usage: [USAGE.md](USAGE.md)
- Production: [PRODUCTION.md](PRODUCTION.md)
