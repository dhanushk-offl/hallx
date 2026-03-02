from hallx.retry import build_recommendation


def test_recommendation_retry_for_high_risk() -> None:
    recommendation = build_recommendation(
        confidence=0.2,
        risk_level="high",
        scores={"schema": 0.3, "consistency": 0.4, "grounding": 0.2},
        issues=["wrong type at '<root>': expected string"],
    )

    assert recommendation["action"] == "retry"
    assert recommendation["suggested_temperature"] == 0.2
    assert "Force JSON mode" in recommendation["suggestions"]
    assert "Switch model" in recommendation["suggestions"]


def test_recommendation_proceed_for_low_risk() -> None:
    recommendation = build_recommendation(
        confidence=0.92,
        risk_level="low",
        scores={"schema": 1.0, "consistency": 1.0, "grounding": 0.95},
        issues=[],
    )

    assert recommendation["action"] == "proceed"
    assert isinstance(recommendation["suggestions"], list)
