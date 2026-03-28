# Contributing to hallx

Thank you for contributing to `hallx`.

This project values focused PRs, test-backed changes, and clear documentation updates.

## Before You Start

- Review the [Code of Conduct](CODE_OF_CONDUCT.md).
- Check existing issues and discussions before opening a new one.
- For bugs and features, use the issue templates in `.github/ISSUE_TEMPLATE/`.

## Development Setup

```bash
pip install -e .[dev]
python -m pytest
```

## Branch and PR Workflow

1. Fork the repository.
2. Create a branch from `main` with a descriptive name:
   - `fix/<short-description>`
   - `feat/<short-description>`
   - `docs/<short-description>`
3. Make your changes and add/update tests.
4. Run local checks.
5. Open a pull request using the PR template.

## Pull Request Expectations

- Keep PR scope small and reviewable.
- Include context: what changed and why.
- Link related issues when applicable.
- Update docs for behavior or API changes.
- Avoid unrelated refactors in the same PR.

## PR Checklist

- Tests pass locally: `python -m pytest`
- Public behavior is covered by tests
- README/docs updated if needed
- Breaking changes clearly documented

## Commit Message Guidance

Conventional style is recommended:

- `feat: add ollama adapter`
- `fix: penalize skipped checks in confidence score`
- `docs: update usage guide for safety profiles`

## Reporting Bugs

Use `Bug report` template and include:

- minimal reproducible example
- expected vs actual behavior
- environment details (OS, Python version, package version)
- logs/tracebacks when available

## Suggesting Features

Use `Feature request` template and include:

- problem statement
- proposed API or behavior
- expected impact and alternatives considered

## Security Issues

Do not report security issues in public issues.

Use:
`https://github.com/dhanushk-offl/hallx/security/advisories/new`

## References

- Issue templates: `.github/ISSUE_TEMPLATE/`
- PR template: `.github/pull_request_template.md`
- Usage docs: `docs/USAGE.md`
