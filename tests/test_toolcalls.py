"""Tests for tool-call validation (hallx.toolcalls)."""

import pytest

from hallx.toolcalls import check_tool_call, score_tool_calls
from hallx.types import ToolCall, ToolCallResult


TOOLS = {
    "get_weather": {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "unit": {"type": "string", "enum": ["c", "f"]},
        },
        "required": ["city"],
        "additionalProperties": False,
    },
    "send_email": {
        "parameters": {
            "type": "object",
            "properties": {"to": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to"],
        }
    },
}


def test_valid_call_scores_full() -> None:
    result = score_tool_calls([ToolCall("get_weather", {"city": "Paris"})], TOOLS)

    assert isinstance(result, ToolCallResult)
    assert result.score == pytest.approx(1.0)
    assert result.verdicts[0].status == "ok"
    assert result.issues == []


def test_accepts_raw_pair_and_openai_style() -> None:
    pair = score_tool_calls([("get_weather", {"city": "Paris"})], TOOLS)
    openai = score_tool_calls(
        [{"function": {"name": "get_weather", "arguments": '{"city": "Paris"}'}}], TOOLS
    )

    assert pair.verdicts[0].status == "ok"
    assert openai.verdicts[0].status == "ok"


def test_unknown_tool_is_blocked() -> None:
    result = score_tool_calls([{"name": "get_weathr", "arguments": "{}"}], TOOLS)

    assert result.verdicts[0].status == "unknown_tool"
    assert result.recommendation["action"] == "block"
    assert "get_weathr" in result.issues[0]


def test_wrong_argument_type_flags_invalid() -> None:
    result = score_tool_calls([{"name": "get_weather", "arguments": '{"city": 123}'}], TOOLS)

    assert result.verdicts[0].status == "invalid_arguments"
    assert result.recommendation["action"] == "fix"
    assert result.score < 1.0
    assert any("city" in issue for issue in result.verdicts[0].issues)


def test_enum_violation_is_detected() -> None:
    result = score_tool_calls(
        [{"name": "get_weather", "arguments": '{"city": "Paris", "unit": "k"}'}], TOOLS
    )

    assert result.verdicts[0].status == "invalid_arguments"
    assert any("enum" in issue for issue in result.verdicts[0].issues)


def test_missing_required_field_is_detected() -> None:
    result = score_tool_calls([("get_weather", {})], TOOLS)

    assert result.verdicts[0].status == "invalid_arguments"
    assert any("missing" in issue for issue in result.verdicts[0].issues)


def test_unexpected_field_is_detected() -> None:
    result = score_tool_calls(
        [{"name": "get_weather", "arguments": '{"city": "Paris", "zip": 75001}'}], TOOLS
    )

    assert result.verdicts[0].status == "invalid_arguments"
    assert any("extra" in issue for issue in result.verdicts[0].issues)


def test_malformed_json_arguments() -> None:
    result = check_tool_call([ToolCall("get_weather", "not json")], TOOLS)

    assert result.verdicts[0].status == "malformed"


def test_json_array_or_scalar_arguments_rejected() -> None:
    array = check_tool_call([ToolCall("get_weather", "[]")], TOOLS)
    scalar = check_tool_call([ToolCall("get_weather", "false")], TOOLS)
    number = check_tool_call([ToolCall("get_weather", "7")], TOOLS)

    assert array.verdicts[0].status == "malformed"
    assert scalar.verdicts[0].status == "malformed"
    assert number.verdicts[0].status == "malformed"
    assert all("object" in verdict.issues[0] for verdict in (array, scalar, number))


def test_raw_arguments_used_when_arguments_missing() -> None:
    result = check_tool_call(
        [ToolCall("get_weather", arguments=None, raw_arguments='{"city": "London"}')], TOOLS
    )

    assert result.verdicts[0].status == "ok"
    assert result.score == pytest.approx(1.0)


def test_raw_arguments_missing_falls_back_to_empty_object() -> None:
    result = check_tool_call(
        [ToolCall("get_weather", arguments=None, raw_arguments=None)], TOOLS
    )

    assert result.verdicts[0].status == "invalid_arguments"


def test_openai_parameters_wrapper_resolved() -> None:
    result = score_tool_calls(
        [{"function": {"name": "send_email", "arguments": '{"to": "x@y.z"}'}}], TOOLS
    )

    assert result.verdicts[0].status == "ok"


def test_no_tool_calls_allowed_bare() -> None:
    result = score_tool_calls([], TOOLS)

    assert result.verdicts == []
    assert result.score == pytest.approx(0.0)


def test_tools_must_be_non_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        score_tool_calls([("get_weather", {})], {})


def test_bad_schema_definition_blocks() -> None:
    result = score_tool_calls(
        [{"name": "get_weather", "arguments": "{}"}],
        {"get_weather": {"parameters": "not a mapping"}},
    )

    assert result.verdicts[0].status == "invalid_definition"
    assert result.recommendation["action"] == "block"
    assert result.score == pytest.approx(0.0)


def test_parameters_wrapper_preserves_extra_schema_keys() -> None:
    tools = {
        "tool": {
            "parameters": {
                "type": "object",
                "properties": {"q": {"type": "string"}},
                "required": ["q"],
                "additionalProperties": False,
            }
        }
    }
    result = check_tool_call([ToolCall("tool", {"q": "hi", "extra": 1})], tools)

    assert result.verdicts[0].status == "invalid_arguments"
    assert any("extra" in issue for issue in result.verdicts[0].issues)