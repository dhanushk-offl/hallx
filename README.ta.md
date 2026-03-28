# hallx (தமிழ்)

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` என்பது LLM output-களுக்கான hallucination risk scoring library.

## இது என்ன செய்கிறது

- `confidence` score (`0.0` முதல் `1.0`)
- `risk_level` (`high`, `medium`, `low`)
- `issues` (எந்த signal பலவீனமாக இருந்தது என்பதை காட்டும்)
- `recommendation` (`proceed`/`retry` போன்ற policy output)

## முக்கிய signal-கள்

- `schema`: JSON structure சரியா?
- `consistency`: பல முறை generate செய்தால் output நிலைத்திருக்கிறதா?
- `grounding`: பதில் context evidence-ஐ ஆதரிக்கிறதா?

## கணக்கீட்டு முறை

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

## விரைவான தொடக்கம்

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

## Safety profiles

- `fast`: குறைந்த latency
- `balanced`: பொதுவான பயன்பாடு (default)
- `strict`: அதிக கவனத்துடன் scoring

## Feedback + Calibration

`hallx` மூலம் review செய்யப்பட்ட முடிவுகளை SQLite-ல் சேமித்து threshold tuning செய்யலாம்:

- `record_outcome(...)`
- `calibration_report(...)`

Default DB path:

- Env: `HALLX_FEEDBACK_DB`
- Windows: `%LOCALAPPDATA%\hallx\feedback.sqlite3`
- macOS: `~/Library/Application Support/hallx/feedback.sqlite3`
- Linux/Server: `~/.local/share/hallx/feedback.sqlite3` (அல்லது `XDG_DATA_HOME`)

## உதவிக்கான இணைப்புகள்

- English README: [README.md](README.md)
- Usage Guide: [docs/USAGE.md](docs/USAGE.md)
- Production Notes: [docs/PRODUCTION.md](docs/PRODUCTION.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
