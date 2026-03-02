"""Core Hallx API."""

import json
from typing import Any, Callable, Iterable, Mapping, Optional

from hallx.consistency import check_consistency, check_consistency_async
from hallx.grounding import check_grounding
from hallx.retry import build_recommendation
from hallx.schema import validate_schema, validate_schema_detailed
from hallx.scoring import combine_scores, resolve_weights, risk_level_from_confidence
from hallx.types import HallxHighRiskError, HallxResult, LLMAdapter, SchemaValidationResult


class Hallx:
    """Hallucination-risk checker with sync and async APIs."""

    def __init__(
        self,
        weights: Optional[Mapping[str, float]] = None,
        strict: bool = False,
    ) -> None:
        self._weights = resolve_weights(weights)
        self._strict = strict

    def check(
        self,
        prompt: str,
        response: Any,
        context: Optional[Iterable[str]] = None,
        schema: Optional[Mapping[str, Any]] = None,
        llm_callable: Optional[Callable[..., str]] = None,
        llm_adapter: Optional[LLMAdapter] = None,
        consistency_runs: int = 3,
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

        consistency_score, consistency_issues = check_consistency(
            prompt=prompt,
            llm_callable=chosen_callable,
            runs=consistency_runs,
            llm_kwargs=llm_kwargs,
            embedding_callable=embedding_callable,
        )

        grounding_score, grounding_issues = check_grounding(
            response=response_text,
            context_docs=context or [],
            embedding_callable=embedding_callable,
            context_embeddings=context_embeddings,
            allow_web=allow_web_sources,
        )

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
        consistency_runs: int = 3,
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

        consistency_score, consistency_issues = await check_consistency_async(
            prompt=prompt,
            llm_callable=chosen_callable,
            runs=consistency_runs,
            llm_kwargs=llm_kwargs,
            embedding_callable=embedding_callable,
        )

        grounding_score, grounding_issues = check_grounding(
            response=response_text,
            context_docs=context or [],
            embedding_callable=embedding_callable,
            context_embeddings=context_embeddings,
            allow_web=allow_web_sources,
        )

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
