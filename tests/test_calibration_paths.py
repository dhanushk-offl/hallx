from pathlib import Path

from hallx.calibration import default_feedback_db_path


def test_default_feedback_db_path_uses_env_override(monkeypatch) -> None:
    target = "/tmp/custom-hallx-feedback.sqlite3"
    monkeypatch.setenv("HALLX_FEEDBACK_DB", target)
    assert default_feedback_db_path() == target


def test_default_feedback_db_path_returns_sqlite_path(monkeypatch) -> None:
    monkeypatch.delenv("HALLX_FEEDBACK_DB", raising=False)
    value = default_feedback_db_path()
    assert value.endswith("feedback.sqlite3")
    assert Path(value).name == "feedback.sqlite3"
