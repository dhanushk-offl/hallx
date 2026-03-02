from hallx import Hallx
from hallx.schema import validate_schema


def test_schema_validation_detects_multiple_issues() -> None:
    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "label": {"type": "string", "enum": ["safe", "unsafe"]},
        },
        "required": ["answer", "label"],
        "additionalProperties": False,
    }
    response = {"answer": 42, "extra": "x"}

    score, issues = validate_schema(response, schema)

    assert 0.0 <= score < 1.0
    assert len(issues) >= 2
    assert any("wrong type" in item for item in issues)
    assert any("missing field" in item for item in issues)
    assert any("unexpected extra field" in item for item in issues)


def test_schema_validation_success() -> None:
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    }

    score, issues = validate_schema({"answer": "ok"}, schema)

    assert score == 1.0
    assert issues == []


def test_check_json_detects_null_injection() -> None:
    checker = Hallx()
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    }

    report = checker.check_json(response={"answer": None}, schema=schema)

    assert report.score < 1.0
    assert report.is_valid is False
    assert any("null injection" in issue for issue in report.issues)
