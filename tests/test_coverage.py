import pytest

from hallx import Hallx, HallxHighRiskError


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.asyncio
async def test_coverage_and_verdicts(async_mode: bool) -> None:
    async def run(**kwargs):
        checker = Hallx()
        if async_mode:
            return await checker.check_async(prompt="p", response="answer", **kwargs)
        return checker.check(prompt="p", response="answer", **kwargs)

    no_checks = await run(context=[" ", ""])
    assert no_checks.risk_level == "insufficient_evidence"
    assert no_checks.recommendation["action"] == "review"
    assert all(item.status == "skipped" and item.reason for item in no_checks.coverage.values())

    schema_only = await run(schema={"type": "integer"})
    assert schema_only.coverage["schema"].status == "evaluated"
    assert schema_only.risk_level == "insufficient_evidence"
    assert schema_only.scores["schema"] < 1

    grounding_only = await run(context=["answer"])
    assert grounding_only.coverage["grounding"].status == "evaluated"
    assert grounding_only.risk_level != "insufficient_evidence"

    consistency_only = await run(llm_callable=lambda _: "answer")
    assert consistency_only.coverage["consistency"].status == "evaluated"
    assert consistency_only.risk_level != "insufficient_evidence"

    all_checks = await run(context=["answer"], schema={"type": "string"},
                           llm_callable=lambda _: "answer")
    assert all(item.status == "evaluated" and item.reason is None
               for item in all_checks.coverage.values())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.asyncio
async def test_required_checks_and_gates(async_mode: bool) -> None:
    checker = Hallx(required_checks={"grounding", "schema"})
    kwargs = {"prompt": "p", "response": "answer", "llm_callable": lambda _: "answer"}
    result = await checker.check_async(**kwargs) if async_mode else checker.check(**kwargs)
    assert result.risk_level == "insufficient_evidence"
    assert "Run required grounding check" in result.recommendation["suggestions"]
    assert "Run required schema check" in result.recommendation["suggestions"]
    with pytest.raises(HallxHighRiskError, match="insufficient evidence"):
        checker.assert_safe(result, threshold=0)

    strict = Hallx(strict=True)
    with pytest.raises(HallxHighRiskError, match="insufficient_evidence"):
        if async_mode:
            await strict.check_async(prompt="p", response="answer")
        else:
            strict.check(prompt="p", response="answer")

    high = Hallx(weights={"schema": 0, "grounding": 1, "consistency": 0}, skip_penalty=1)
    result = await high.check_async(prompt="p", response="answer") if async_mode else high.check(prompt="p", response="answer")
    assert result.risk_level == "high"
    assert result.recommendation["action"] == "retry"
    assert any("insufficient evidence" in issue for issue in result.issues)


@pytest.mark.parametrize("required", ["grounding", ["unknown"], [None]])
def test_invalid_required_checks(required) -> None:
    with pytest.raises(ValueError):
        Hallx(required_checks=required)


def test_provider_failure_propagates() -> None:
    def fail(_):
        raise RuntimeError("provider unavailable")

    with pytest.raises(RuntimeError, match="provider unavailable"):
        Hallx().check(prompt="p", response="r", llm_callable=fail)


def test_insufficient_evidence_feedback(tmp_path) -> None:
    checker = Hallx(feedback_db_path=str(tmp_path / "feedback.sqlite3"))
    assert "insufficient_evidence" in checker.calibration_report()["by_risk_level"]
    result = checker.check(prompt="p", response="r")
    checker.record_outcome(result, "hallucinated")
    bucket = checker.calibration_report()["by_risk_level"]["insufficient_evidence"]
    assert bucket["count"] == 1
    assert bucket["hallucinated"] == 1
