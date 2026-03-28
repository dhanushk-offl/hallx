import math

import pytest

from hallx import Hallx
from hallx.adapters import OpenAIAdapter
from hallx.scoring import combine_scores, resolve_weights


def test_resolve_weights_normalizes_sum_to_one() -> None:
    resolved = resolve_weights({"schema": 2.0, "consistency": 1.0, "grounding": 1.0})
    assert sum(resolved.values()) == pytest.approx(1.0)
    assert resolved["schema"] == pytest.approx(0.5)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, "x"])
def test_resolve_weights_rejects_non_finite_or_non_numeric_values(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        resolve_weights({"schema": bad, "consistency": 0.5, "grounding": 0.5})  # type: ignore[arg-type]


def test_combine_scores_clamps_score_inputs() -> None:
    score = combine_scores(
        scores={"schema": 2.0, "consistency": -1.0, "grounding": 0.5},
        weights={"schema": 1.0, "consistency": 1.0, "grounding": 2.0},
    )
    assert score == pytest.approx(0.5)


def test_combine_scores_rejects_non_finite_score() -> None:
    with pytest.raises(ValueError):
        combine_scores(
            scores={"schema": 1.0, "consistency": math.nan, "grounding": 1.0},
            weights={"schema": 1.0, "consistency": 1.0, "grounding": 1.0},
        )


def test_check_json_accepts_json_string_payload() -> None:
    checker = Hallx()
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    }
    report = checker.check_json(response='{"answer":"ok"}', schema=schema)
    assert report.is_valid is True
    assert report.score == 1.0


def test_hallx_rejects_non_serializable_response() -> None:
    checker = Hallx()
    with pytest.raises(TypeError):
        checker.check(prompt="p", response=object())


def test_adapter_from_env_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        OpenAIAdapter.from_env(model="gpt-test", env_key_name="OPENAI_API_KEY")
