import pytest

from hallx import Hallx
from hallx.scoring import combine_scores, risk_level_from_confidence
from hallx.types import HallxHighRiskError


def test_score_aggregation_and_risk_mapping() -> None:
    confidence = combine_scores(
        scores={"schema": 1.0, "consistency": 0.5, "grounding": 0.0},
        weights={"schema": 0.3, "consistency": 0.4, "grounding": 0.3},
    )

    assert confidence == pytest.approx(0.5)
    assert risk_level_from_confidence(0.2) == "high"
    assert risk_level_from_confidence(0.6) == "medium"
    assert risk_level_from_confidence(0.9) == "low"


def test_hallx_check_and_strict_mode() -> None:
    checker = Hallx(strict=True)

    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    }

    outputs = ["alpha", "zeta", "omega"]

    def unstable_llm(_: str) -> str:
        return outputs.pop(0)

    with pytest.raises(HallxHighRiskError):
        checker.check(
            prompt="return structured answer",
            response={"bad": 1},
            context=["Known answer is hello."],
            schema=schema,
            llm_callable=unstable_llm,
            consistency_runs=3,
        )


def test_hallx_assert_safe() -> None:
    checker = Hallx()
    outputs = ["one", "two", "three"]

    def unstable_llm(_: str) -> str:
        return outputs.pop(0)

    result = checker.check(
        prompt="p",
        response="completely unrelated",
        context=["known context"],
        llm_callable=unstable_llm,
        consistency_runs=3,
    )

    assert result.recommendation["action"] in {"proceed", "retry"}
    assert "suggested_temperature" in result.recommendation

    checker.assert_safe(result, threshold=0.2)

    with pytest.raises(HallxHighRiskError):
        checker.assert_safe(result, threshold=0.9)


def test_skip_penalty_reduces_confidence_when_checks_are_skipped() -> None:
    checker = Hallx(
        profile="balanced",
        weights={"schema": 0.0, "consistency": 0.5, "grounding": 0.5},
    )
    result = checker.check(prompt="p", response="r", context=None, llm_callable=None)

    assert result.confidence == pytest.approx(0.75)
    assert result.risk_level == "low"
    assert any("penalized" in issue for issue in result.issues)


def test_profile_changes_default_consistency_runs() -> None:
    calls = {"count": 0}

    def stable_llm(_: str) -> str:
        calls["count"] += 1
        return "ok"

    Hallx(profile="fast").check(
        prompt="p",
        response="ok",
        context=["ok"],
        llm_callable=stable_llm,
        consistency_runs=None,
    )
    assert calls["count"] == 2

    calls["count"] = 0
    Hallx(profile="strict").check(
        prompt="p",
        response="ok",
        context=["ok"],
        llm_callable=stable_llm,
        consistency_runs=None,
    )
    assert calls["count"] == 4


def test_invalid_profile_raises() -> None:
    with pytest.raises(ValueError):
        Hallx(profile="unknown")


@pytest.mark.asyncio
async def test_hallx_async_flow() -> None:
    checker = Hallx(weights={"schema": 0.3, "consistency": 0.4, "grounding": 0.3})

    async def llm(_: str) -> str:
        return "The sky is blue."

    result = await checker.check_async(
        prompt="What color is the sky?",
        response="The sky is blue.",
        context=["The sky is often perceived as blue during the day."],
        llm_callable=llm,
        consistency_runs=3,
    )

    assert 0.0 <= result.confidence <= 1.0
    assert result.risk_level in {"high", "medium", "low"}
    assert isinstance(result.breakdown, dict)
    assert isinstance(result.recommendation, dict)
