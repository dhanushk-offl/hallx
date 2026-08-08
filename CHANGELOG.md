# Changelog

## [1.1.0] - 2026-08-09

### Added
- Claim-level grounding (`hallx.attribution`): sentence-span claim extraction with per-claim `supported` / `weak` / `unsupported` verdicts plus evidence snippets
- Pluggable faithfulness verifiers: `LocalNLIChecker` (local NLI via optional `hallx[nli]` extra) and `GroundingJudge` LLM-as-judge (`hallx.judge`)
- Tool-call validation (`hallx.toolcalls`, `Hallx.check_tool_call`): hallucinated tool-name detection and argument-schema validation with `ok` / `invalid_arguments` / `malformed` / `invalid_definition` / `unknown_tool` verdicts
- Async claim-grounding and grounding paths with `asyncio.gather` backends
- New typed models: `Claim`, `ClaimGroundingResult`, `ToolCall`, `ToolCallVerdict`, `ToolCallResult`
- Python 3.9-compatible annotations across tests and samples

### Fixed
- Removed unused `requests==2.20.0` pin that broke dependency resolution; moved to security-fixed pinned `requests` per Python version
- `filtered_count` now reported correctly when all claims are filtered
- Claims with embeddings but no `embedding_callable` raise instead of silently fuzzy-falling back
- `GroundingJudge` score parsing now prefers labeled scores and JSON-quotes evidence/hypothesis to block prompt injection
- Tool-call validation rejects non-object JSON arguments and uses `raw_arguments` when `arguments` is absent

### Changed
- `check` / `check_async` accept `claims=True` and `verifier=...`; evidence lands on `result.evidence`
- Deduplicated sync/async embedding helpers and aligned filtered-sentence issue wording

## [1.0.4] - 2026-06-01

### Added
- Project website with SEO, FAQ, sample pages, and sitemap
- OpenGraph image for social sharing
- `robots.txt` for web crawlers
- Monthly download stats badge (via pypistats) on website and README

### Changed
- Switched release CI/CD from PyPI secrets to OIDC-based trusted publishing
- Updated Buy Me a Coffee username in website footer

## [1.0.3] - 2026-05-23

### Added
- Ollama adapter support
- Async OpenAI adapter with context support
- Hallx workflow diagram documentation
- `[dev]` extras (pytest, build, twine)

### Changed
- Improved trust scoring pipeline
- Enhanced documentation with Tamil translations and code of conduct
- Updated README with feature badges and new examples

## [1.0.2] - 2026-05-20

### Fixed
- PyPI README rendering issues
- Documentation polish and formatting

## [1.0.1] - 2026-05-20

### Added
- Initial PyPI release
- Core hallucination risk scoring engine
- JSON schema validation
- RapidFuzz-based similarity scoring
- OpenAI and generic LLM adapters
