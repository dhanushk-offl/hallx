# hallx (தமிழ்)

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` என்பது LLM output-களுக்கான risk scoring guardrail library.  
Production சூழலில் ஒரு output-ஐ நம்புவதற்கு முன்:

`இது பாதுகாப்பான பதிலா, இல்லையா?`

என்பதற்கான நடைமுறை பதிலை இது தருகிறது.

## ஏன் Hallx உருவாக்கப்பட்டது

பெரும்பாலான LLM output பிரச்சினைகள் மிகவும் நுணுக்கமானவை:

- பதில் மிகவும் நம்பகமாக தோன்றும், ஆனால் context-ல் ஆதாரம் இருக்காது
- JSON format பார்க்க சரியாக இருந்தாலும் strict parser-ல் உடைந்து போகும்
- ஒரே prompt-க்கு repeated output-கள் மிக வேறுபடும்

இந்த risk-ஐ அளவிடாமல் production-ல் output பயன்படுத்துவது கடினம்.  
Hallx இந்த இடத்தில் policy முடிவு எடுக்க உதவுகிறது:

- score செய்ய
- issues காண்பிக்க
- proceed/retry தீர்மானிக்க
- review feedback மூலம் policy tune செய்ய

## Hallx என்ன செய்கிறது

| திறன் | output |
|---|---|
| Risk scoring | `confidence` (`0.0` முதல் `1.0`) |
| Risk label | `risk_level` (`high`, `medium`, `low`) |
| Diagnostics | `issues` |
| Runtime policy hints | `recommendation` |
| Governance loop | feedback storage + calibration report |

## யாருக்காக இது

Hallx பயன்படும் குழுக்கள்:

- RAG/chat app உருவாக்கும் அணிகள்
- JSON output-ஐ machine workflows-க்கு கொடுக்கும் backend அணிகள்
- retry/block policy அமைக்கும் ops/QA அணிகள்
- LLM output மூலம் side effect செய்கிற systems (DB write, automation)

குறிப்பு: medical/legal/financial போன்ற high-stakes துறைகளில் domain-specific validation அவசியம்.

## Scoring Model

Hallx மூன்று heuristic signal-கள் அடிப்படையில் score கணக்கிடுகிறது:

- `schema`: structure சரியா?
- `consistency`: repeated output நிலைத்திருக்கிறதா?
- `grounding`: claims context-ஐ ஆதரிக்கிறதா?

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

Skipped checks-க்கு penalty சேர்க்கப்படும் (partial analysis over-trust தவிர்க்க).

## End-to-End Workflow

![Hallx workflow](images/hallx-working-flow.svg)

1. Prompt + optional context/schema பெறுக.
2. Adapter/callable மூலம் response உருவாக்குக.
3. `schema`, `consistency`, `grounding` checks ஓட்டுக.
4. `confidence` + `risk_level` பெறுக.
5. `recommendation` அடிப்படையில் proceed/retry policy apply செய்யவும்.
6. Reviewed outcome-ஐ save செய்து `calibration_report` மூலம் threshold tune செய்யவும்.

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

| Profile | நோக்கம் | Default `consistency_runs` | Skip penalty |
|---|---|---:|---:|
| `fast` | குறைந்த latency | 2 | 0.15 |
| `balanced` | பொதுப் பயன்பாடு | 3 | 0.25 |
| `strict` | அதிக கட்டுப்பாடு | 4 | 0.40 |

## மேலும் படிக்க

- English docs: [README.en.md](README.en.md)
- Malayalam docs: [README.ml.md](README.ml.md)
- Usage guide: [USAGE.md](USAGE.md)
- Production notes: [PRODUCTION.md](PRODUCTION.md)
