"""Core Hallx API."""

import json
from typing import Any, Callable, Iterable, Mapping, Optional

from hallx.calibration import FeedbackStore
from hallx.consistency import check_consistency, check_consistency_async
from hallx.grounding import check_grounding
from hallx.retry import build_recommendation
from hallx.schema import validate_schema, validate_schema_detailed
from hallx.scoring import combine_scores, resolve_weights, risk_level_from_confidence
from hallx.types import HallxHighRiskError, HallxResult, LLMAdapter, SchemaValidationResult


_PROFILE_WEIGHTS = {
    "fast": {"schema": 0.45, "consistency": 0.35, "grounding": 0.20},
    "balanced": {"schema": 0.34, "consistency": 0.33, "grounding": 0.33},
    "strict": {"schema": 0.25, "consistency": 0.35, "grounding": 0.40},
}
_PROFILE_CONSISTENCY_RUNS = {"fast": 2, "balanced": 3, "strict": 4}
_PROFILE_SKIP_PENALTY = {"fast": 0.15, "balanced": 0.25, "strict": 0.40}


class Hallx:
    """Hallucination-risk checker with sync and async APIs."""

    def __init__(
        self,
        weights: Optional[Mapping[str, float]] = None,
        profile: str = "balanced",
        strict: bool = False,
        skip_penalty: Optional[float] = None,
        feedback_db_path: Optional[str] = None,
    ) -> None:
        normalized_profile = _normalize_profile(profile)
        chosen_weights = weights if weights is not None else _PROFILE_WEIGHTS[normalized_profile]
        self._weights = resolve_weights(chosen_weights)
        self._profile = normalized_profile
        self._default_consistency_runs = _PROFILE_CONSISTENCY_RUNS[normalized_profile]
        self._skip_penalty = _resolve_skip_penalty(skip_penalty, normalized_profile)
        self._strict = strict
        self._feedback_db_path = feedback_db_path
        self._feedback_store: Optional[FeedbackStore] = None

    def check(
        self,
        prompt: str,
        response: Any,
        context: Optional[Iterable[str]] = None,
        schema: Optional[Mapping[str, Any]] = None,
        llm_callable: Optional[Callable[..., str]] = None,
        llm_adapter: Optional[LLMAdapter] = None,
        consistency_runs: Optional[int] = None,
        llm_kwargs: Optional[Mapping[str, Any]] = None,
        embedding_callable: Optional[Callable[[str], Any]] = None,
        context_embeddings: Optional[list[list[float]]] = None,
        allow_web_sources: bool = False,
    ) -> HallxResult:
        """Run all enabled checks and return a typed result."""
        response_text, parsed_response = _coerce_response(response)
        chosen_callable = llm_callable or (llm_adapter.generate if llm_adapter is not None else None)

        schema_score = 1.0
        schema_issues: list[str] = []
        if schema is not None:
            schema_score, schema_issues = validate_schema(parsed_response, schema)

        runs = consistency_runs if consistency_runs is not None else self._default_consistency_runs

        consistency_score, consistency_issues = check_consistency(
            prompt=prompt,
            llm_callable=chosen_callable,
            runs=runs,
            llm_kwargs=llm_kwargs,
            embedding_callable=embedding_callable,
        )
        consistency_score, consistency_penalty_issue = _apply_skip_penalty(
            score=consistency_score,
            issues=consistency_issues,
            check_name="consistency",
            skip_penalty=self._skip_penalty,
        )
        if consistency_penalty_issue is not None:
            consistency_issues.append(consistency_penalty_issue)

        grounding_score, grounding_issues = check_grounding(
            response=response_text,
            context_docs=context or [],
            embedding_callable=embedding_callable,
            context_embeddings=context_embeddings,
            allow_web=allow_web_sources,
        )
        grounding_score, grounding_penalty_issue = _apply_skip_penalty(
            score=grounding_score,
            issues=grounding_issues,
            check_name="grounding",
            skip_penalty=self._skip_penalty,
        )
        if grounding_penalty_issue is not None:
            grounding_issues.append(grounding_penalty_issue)

        scores = {
            "schema": schema_score,
            "consistency": consistency_score,
            "grounding": grounding_score,
        }
        confidence = combine_scores(scores, self._weights)
        risk_level = risk_level_from_confidence(confidence)

        issues = schema_issues + consistency_issues + grounding_issues
        recommendation = build_recommendation(
            confidence=confidence,
            risk_level=risk_level,
            scores=scores,
            issues=issues,
        )
        result = HallxResult(
            confidence=confidence,
            risk_level=risk_level,
            scores=scores,
            issues=issues,
            recommendation=recommendation,
        )

        if self._strict and risk_level == "high":
            raise HallxHighRiskError(
                f"high hallucination risk detected with confidence={confidence:.3f}: {issues}"
            )

        return result

    async def check_async(
        self,
        prompt: str,
        response: Any,
        context: Optional[Iterable[str]] = None,
        schema: Optional[Mapping[str, Any]] = None,
        llm_callable: Optional[Callable[..., Any]] = None,
        llm_adapter: Optional[LLMAdapter] = None,
        consistency_runs: Optional[int] = None,
        llm_kwargs: Optional[Mapping[str, Any]] = None,
        embedding_callable: Optional[Callable[[str], Any]] = None,
        context_embeddings: Optional[list[list[float]]] = None,
        allow_web_sources: bool = False,
    ) -> HallxResult:
        """Async version of ``check`` supporting sync or async LLM callables."""
        response_text, parsed_response = _coerce_response(response)
        chosen_callable = llm_callable or (llm_adapter.agenerate if llm_adapter is not None else None)

        schema_score = 1.0
        schema_issues: list[str] = []
        if schema is not None:
            schema_score, schema_issues = validate_schema(parsed_response, schema)

        runs = consistency_runs if consistency_runs is not None else self._default_consistency_runs

        consistency_score, consistency_issues = await check_consistency_async(
            prompt=prompt,
            llm_callable=chosen_callable,
            runs=runs,
            llm_kwargs=llm_kwargs,
            embedding_callable=embedding_callable,
        )
        consistency_score, consistency_penalty_issue = _apply_skip_penalty(
            score=consistency_score,
            issues=consistency_issues,
            check_name="consistency",
            skip_penalty=self._skip_penalty,
        )
        if consistency_penalty_issue is not None:
            consistency_issues.append(consistency_penalty_issue)

        grounding_score, grounding_issues = check_grounding(
            response=response_text,
            context_docs=context or [],
            embedding_callable=embedding_callable,
            context_embeddings=context_embeddings,
            allow_web=allow_web_sources,
        )
        grounding_score, grounding_penalty_issue = _apply_skip_penalty(
            score=grounding_score,
            issues=grounding_issues,
            check_name="grounding",
            skip_penalty=self._skip_penalty,
        )
        if grounding_penalty_issue is not None:
            grounding_issues.append(grounding_penalty_issue)

        scores = {
            "schema": schema_score,
            "consistency": consistency_score,
            "grounding": grounding_score,
        }
        confidence = combine_scores(scores, self._weights)
        risk_level = risk_level_from_confidence(confidence)

        issues = schema_issues + consistency_issues + grounding_issues
        recommendation = build_recommendation(
            confidence=confidence,
            risk_level=risk_level,
            scores=scores,
            issues=issues,
        )
        result = HallxResult(
            confidence=confidence,
            risk_level=risk_level,
            scores=scores,
            issues=issues,
            recommendation=recommendation,
        )

        if self._strict and risk_level == "high":
            raise HallxHighRiskError(
                f"high hallucination risk detected with confidence={confidence:.3f}: {issues}"
            )

        return result

    def check_json(self, response: Any, schema: Mapping[str, Any]) -> SchemaValidationResult:
        """Validate JSON response payload against schema."""
        _, parsed_response = _coerce_response(response)
        return validate_schema_detailed(parsed_response, schema)

    def assert_safe(self, result: HallxResult, threshold: float = 0.4) -> None:
        """Raise ``HallxHighRiskError`` if confidence is below threshold."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if result.confidence < threshold:
            raise HallxHighRiskError(
                f"confidence {result.confidence:.3f} is below threshold {threshold:.3f}"
            )

    def record_outcome(
        self,
        result: HallxResult,
        label: str,
        metadata: Optional[Mapping[str, Any]] = None,
        prompt: Optional[str] = None,
        response_excerpt: Optional[str] = None,
    ) -> int:
        """Store human-reviewed outcome in feedback DB and return row id."""
        store = self._get_feedback_store()
        return store.record_outcome(
            result=result,
            label=label,
            metadata=metadata,
            prompt=prompt,
            response_excerpt=response_excerpt,
        )

    def calibration_report(self, window_days: Optional[int] = None) -> Mapping[str, Any]:
        """Return aggregate calibration metrics from stored feedback."""
        store = self._get_feedback_store()
        return store.calibration_report(window_days=window_days)

    def _get_feedback_store(self) -> FeedbackStore:
        if self._feedback_store is None:
            self._feedback_store = FeedbackStore(self._feedback_db_path)
        return self._feedback_store


def _coerce_response(response: Any) -> tuple[str, Any]:
    """Return response text and parsed object for schema checks."""
    if isinstance(response, str):
        response_text = response
        parsed = _try_parse_json(response)
        return response_text, parsed

    if isinstance(response, (dict, list, int, float, bool)) or response is None:
        return json.dumps(response, ensure_ascii=True), response

    raise TypeError("response must be JSON-serializable or str")


def _try_parse_json(value: str) -> Any:
    """Parse JSON string when possible, otherwise return raw string."""
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def _normalize_profile(profile: str) -> str:
    normalized = profile.strip().lower()
    if normalized not in _PROFILE_WEIGHTS:
        raise ValueError("profile must be one of: fast, balanced, strict")
    return normalized


def _resolve_skip_penalty(skip_penalty: Optional[float], profile: str) -> float:
    if skip_penalty is None:
        return _PROFILE_SKIP_PENALTY[profile]
    value = float(skip_penalty)
    if not 0.0 <= value <= 1.0:
        raise ValueError("skip_penalty must be between 0 and 1")
    return value


def _apply_skip_penalty(
    score: float,
    issues: list[str],
    check_name: str,
    skip_penalty: float,
) -> tuple[float, Optional[str]]:
    skipped = any("skipped" in issue.lower() for issue in issues)
    if not skipped:
        return score, None
    penalized = max(0.0, min(1.0, float(score) - skip_penalty))
    issue = (
        f"{check_name} score penalized by {skip_penalty:.2f} "
        f"because the check was skipped"
    )
    return penalized, issue
