from pathlib import Path

import pytest

from hallx import Hallx
from hallx.types import HallxResult

sqlite3 = pytest.importorskip("sqlite3", exc_type=ImportError)


def _make_result(confidence: float, risk_level: str) -> HallxResult:
    return HallxResult(
        confidence=confidence,
        risk_level=risk_level,
        scores={"schema": 1.0, "consistency": 0.8, "grounding": 0.7},
        issues=[],
        recommendation={"action": "proceed"},
    )


def test_feedback_storage_and_report(tmp_path: Path) -> None:
    db_path = tmp_path / "feedback.sqlite3"
    checker = Hallx(feedback_db_path=str(db_path))

    first_id = checker.record_outcome(
        result=_make_result(0.9, "low"),
        label="correct",
        metadata={"source": "manual_review"},
        prompt="What is 2+2?",
        response_excerpt="4",
    )
    second_id = checker.record_outcome(
        result=_make_result(0.2, "high"),
        label="hallucinated",
        metadata={"source": "manual_review"},
        prompt="Invented claim",
        response_excerpt="According to unknown source...",
    )

    assert first_id > 0
    assert second_id > first_id
    assert db_path.exists()

    report = checker.calibration_report()
    assert report["total"] == 2
    assert report["correct"] == 1
    assert report["hallucinated"] == 1
    assert 0.0 <= report["hallucination_rate"] <= 1.0
    assert report["by_risk_level"]["high"]["count"] == 1
    assert report["by_risk_level"]["low"]["count"] == 1
    assert report["suggested_threshold"] is not None


def test_feedback_label_aliases(tmp_path: Path) -> None:
    checker = Hallx(feedback_db_path=str(tmp_path / "feedback.sqlite3"))
    checker.record_outcome(result=_make_result(0.95, "low"), label="safe")
    checker.record_outcome(result=_make_result(0.1, "high"), label="unsafe")

    report = checker.calibration_report()
    assert report["correct"] == 1
    assert report["hallucinated"] == 1


def test_feedback_invalid_label_raises(tmp_path: Path) -> None:
    checker = Hallx(feedback_db_path=str(tmp_path / "feedback.sqlite3"))
    with pytest.raises(ValueError):
        checker.record_outcome(result=_make_result(0.9, "low"), label="maybe")
