# Contributing to hallx

Thanks for your interest in improving `hallx`.

## How to contribute

1. Fork the repo and create a feature branch.
2. Make your changes with tests.
3. Run the full test suite locally.
4. Open a pull request with a clear summary.

## Local setup

```bash
pip install -e .[dev]
python -m pytest
```

## Contribution expectations

- Keep changes focused and small where possible.
- Add or update tests for behavior changes.
- Keep public APIs and docs in sync.
- Prefer clear naming and explicit error handling.

## Pull request checklist

- Tests pass (`python -m pytest`)
- Docs updated (README/docs) if behavior changed
- No breaking API changes without rationale

## Reporting issues

Open an issue with:
- expected behavior
- actual behavior
- reproduction steps
- Python version and environment details
