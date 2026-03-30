# hallx (Deutsch)

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` ist eine schlanke Guardrail-Bibliothek für LLM-Ausgaben.  
Sie beantwortet vor der Nutzung einer Antwort im Produktivsystem eine zentrale Frage:

`Wie riskant ist diese Ausgabe?`

## Warum Hallx

LLM-Fehler im Betrieb sind oft subtil:

- Antworten wirken plausibel, sind aber nicht durch Evidenz gestützt
- JSON sieht korrekt aus, scheitert jedoch bei strikten Konsumenten
- Mehrfachgenerierungen driften zu stark für zuverlässige Automatisierung

Hallx liefert eine praktische Entscheidungsschicht:

- Antwort bewerten
- Schwachstellen sichtbar machen
- `proceed` vs. `retry` entscheiden
- Schwellenwerte mit Feedback nachschärfen

## Was Hallx liefert

| Funktion | Output |
|---|---|
| Risikobewertung | `confidence` (`0.0` bis `1.0`) |
| Risikokategorie | `risk_level` (`high`, `medium`, `low`) |
| Diagnostik | `issues` |
| Laufzeit-Hinweise | `recommendation` |
| Governance | Feedback-Speicherung + Kalibrierungsbericht |

## Für wen Hallx geeignet ist

- Teams mit RAG-/Chat-Features
- Backends mit maschinenverarbeitetem JSON
- Workflows, in denen LLM-Ausgaben Aktionen auslösen
- Ops-/QA-Teams mit Retry/Block-Policy

Hinweis: In High-Stakes-Domänen (medizinisch/rechtlich/finanziell) ersetzt Hallx keine domänenspezifische Verifikation.

## Scoring-Modell

Hallx kombiniert drei heuristische Signale:

- `schema`: strukturelle Gültigkeit
- `consistency`: Stabilität über Wiederholungen
- `grounding`: Abgleich von Claims mit Kontext

```text
confidence = clamp(
  schema_score * w_schema +
  consistency_score * w_consistency +
  grounding_score * w_grounding,
  0.0, 1.0
)
```

Standardgewichte (`balanced`):
- `w_schema = 0.34`
- `w_consistency = 0.33`
- `w_grounding = 0.33`

Risikomapping:
- `< 0.40` -> `high`
- `< 0.75` -> `medium`
- `>= 0.75` -> `low`

Übersprungene Checks werden standardmäßig abgestraft, um Übervertrauen bei unvollständiger Analyse zu vermeiden.

## End-to-End-Workflow

![Hallx workflow](images/hallx-working-flow.svg)

1. Prompt sowie optionalen Kontext/Schema erfassen.
2. Antwort via Adapter/Callable generieren.
3. `schema`-, `consistency`- und `grounding`-Checks ausführen.
4. `confidence` und `risk_level` berechnen.
5. Policy (`proceed`/`retry`) anwenden.
6. Reviewte Ergebnisse speichern und Schwellenwerte kalibrieren.

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

## Safety-Profile

| Profil | Ziel | Standard `consistency_runs` | Skip-Penalty |
|---|---|---:|---:|
| `fast` | geringere Latenz | 2 | 0.15 |
| `balanced` | allgemeiner Einsatz | 3 | 0.25 |
| `strict` | strengere Kontrolle | 4 | 0.40 |

## Weiterführende Dokumente

- English: [README.en.md](README.en.md)
- தமிழ்: [README.ta.md](README.ta.md)
- മലയാളം: [README.ml.md](README.ml.md)
- Usage: [USAGE.md](USAGE.md)
- Production: [PRODUCTION.md](PRODUCTION.md)
