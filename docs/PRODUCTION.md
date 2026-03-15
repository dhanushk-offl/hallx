# Production Notes

## Runtime controls

- Use `strict=True` to fail fast on high-risk output.
- Use `assert_safe(result, threshold=...)` to enforce custom SLO gates.
- Keep `consistency_runs >= 2`; `3` is a practical default.

## Dependency and release hygiene

```bash
python -m pytest
python -m build
python -m twine check dist/*
```

## Operational recommendations

- Log `confidence`, `risk_level`, and `issues` for observability.
- Treat external URLs in model output as untrusted unless verified.
- Prefer deterministic model settings (`temperature <= 0.3`) in critical flows.
- Run schema validation for machine-consumed outputs.
