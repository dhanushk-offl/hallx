# hallx (മലയാളം)

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` ഒരു LLM output guardrail library ആണ്.  
Production-ൽ ഒരു response ഉപയോഗിക്കുന്നതിന് മുമ്പ്:

`ഇത് വിശ്വസിക്കാവുന്ന output ആണോ?`

എന്ന് വിലയിരുത്താൻ ഇത് സഹായിക്കുന്നു.

## Hallx എന്തിന്

LLM output പ്രശ്നങ്ങൾ പലപ്പോഴും നേരിട്ട് കാണാനാവില്ല:

- response fluent ആണെങ്കിലും evidence ഇല്ലാതെ claim ചെയ്യാം
- JSON നോക്കാൻ ശരിയായ പോലെ തോന്നും, പക്ഷേ parser-ൽ fail ആകാം
- ഒരേ prompt-ൽ repeated output-ൽ സ്ഥിരത ഇല്ലാതാകാം

ഈ risk operational രീതിയിൽ അളക്കാൻ Hallx ഉപയോഗിക്കുന്നു:

- score ലഭിക്കുക
- issue list ലഭിക്കുക
- proceed/retry policy തീരുമാനിക്കുക
- reviewed outcomes വഴി threshold tune ചെയ്യുക

## Hallx എന്ത് നൽകുന്നു

| Capability | Output |
|---|---|
| Risk scoring | `confidence` (`0.0` മുതൽ `1.0`) |
| Risk label | `risk_level` (`high`, `medium`, `low`) |
| Diagnostics | `issues` |
| Action hints | `recommendation` |
| Governance loop | feedback storage + calibration report |

## ആര്ക്ക് ഉപകാരപ്പെടും

Hallx അനുയോജ്യം:

- RAG/chat systems നിർമ്മിക്കുന്ന ടീമുകൾക്ക്
- JSON output machine workflows-ൽ ഉപയോഗിക്കുന്ന backend ടീമുകൾക്ക്
- retry/block policy നിർമ്മിക്കുന്ന ops/QA ടീമുകൾക്ക്
- LLM output side effects trigger ചെയ്യുന്ന systems-ക്ക്

High-stakes domains (medical/legal/financial) ൽ domain-specific validators + human review നിർബന്ധമാണ്.

## Scoring Model

Hallx മൂന്നു heuristic signals ഉപയോഗിക്കുന്നു:

- `schema`: structured output ശരിയാണോ?
- `consistency`: repeated generations സ്ഥിരമാണോ?
- `grounding`: claims, context evidence പിന്തുണയ്ക്കുന്നുണ്ടോ?

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

Skipped checks-ന് penalty നൽകും; അതുവഴി partial analysis over-trust കുറയ്ക്കാം.

## End-to-End Workflow

![Hallx workflow](images/hallx-working-flow.svg)

1. Prompt + optional context/schema എടുക്കുക.
2. Adapter/callable വഴി response generate ചെയ്യുക.
3. `schema`, `consistency`, `grounding` checks നടത്തുക.
4. `confidence` + `risk_level` കണ്ടെത്തുക.
5. `recommendation` അനുസരിച്ച് proceed/retry policy ഉപയോഗിക്കുക.
6. reviewed outcomes save ചെയ്ത് `calibration_report` കൊണ്ട് threshold tune ചെയ്യുക.

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

| Profile | ലക്ഷ്യം | Default `consistency_runs` | Skip penalty |
|---|---|---:|---:|
| `fast` | കുറഞ്ഞ latency | 2 | 0.15 |
| `balanced` | പൊതുവായ ഉപയോഗം | 3 | 0.25 |
| `strict` | കൂടുതൽ കർശന പരിശോധന | 4 | 0.40 |

## കൂടുതൽ രേഖകൾ

- English docs: [README.en.md](README.en.md)
- Tamil docs: [README.ta.md](README.ta.md)
- Usage guide: [USAGE.md](USAGE.md)
- Production notes: [PRODUCTION.md](PRODUCTION.md)
