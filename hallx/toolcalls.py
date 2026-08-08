"""Tool-call validation for agentic LLM workflows.

Detects hallucinated tool names and validates invocation arguments against
declared tool JSON schemas before a call is allowed to execute.
"""

import json
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from rapidfuzz import fuzz

from hallx.schema import validate_schema
from hallx.types import ToolCall, ToolCallResult, ToolCallVerdict


def _normalize_name(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        nested = value.get("name")
        if not isinstance(nested, str):
            function = value.get("function")
            if isinstance(function, Mapping):
                nested = function.get("name")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
        raise TypeError("tool call mapping must include a string 'name'")
    raise TypeError("tool call name must be a string")


def _coerce_arguments(raw: Any) -> Tuple[Any, Optional[str]]:
    if raw is None:
        return None, None
    if isinstance(raw, Mapping):
        return dict(raw), None
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None, "tool arguments are not valid JSON"
        return parsed, None
    return raw, "tool arguments must be a JSON object or object mapping"


def _find_tool_schema(name: str, tools: Mapping[str, Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
    schema = tools.get(name)
    if not isinstance(schema, Mapping):
        return None
    if "parameters" in schema and isinstance(schema["parameters"], Mapping):
        parameters = schema["parameters"]
        resolved: Dict[str, Any] = {
            "type": parameters.get("type", "object"),
            "additionalProperties": parameters.get("additionalProperties", False),
        }
        if "properties" in parameters:
            resolved["properties"] = parameters["properties"]
        if "required" in parameters:
            resolved["required"] = parameters["required"]
        return _coerce_parameters_schema(resolved)
    return _coerce_parameters_schema(schema)


def _coerce_parameters_schema(schema: Mapping[str, Any]) -> Mapping[str, Any]:
    coerced = dict(schema)
    type_value = schema.get("type")
    if type_value is None:
        coerced["type"] = "object"
    props = schema.get("properties")
    if props is not None and not isinstance(props, Mapping):
        coerced.pop("properties", None)
    return coerced


def check_tool_call(
    tool_calls: Sequence[ToolCall],
    tools: Mapping[str, Mapping[str, Any]],
) -> ToolCallResult:
    """Validate tool invocations and return a per-call report.

    ``tools`` maps a tool name to a JSON-Schema style definition. Each schema
    may either be a bare JSON Schema object or an OpenAI-style wrapper with a
    ``parameters`` entry.
    """
    if not tools:
        raise ValueError("tools must be a non-empty mapping of tool name to schema")

    verdicts: List[ToolCallVerdict] = []
    aggregate_issues: List[str] = []
    scores: List[float] = []

    for index, call in enumerate(tool_calls):
        name = call.name
        args, arg_error = _coerce_arguments(call.arguments)

        if name not in tools:
            verdict = _unknown_tool_verdict(index, name, arg_error)
            verdicts.append(verdict)
            issues: List[str] = list(verdict.issues)
            scores.append(verdict.score)
            aggregate_issues.extend(issues)
            continue

        schema = _find_tool_schema(name, tools)
        if schema is None:
            verdict = ToolCallVerdict(
                call_index=index, name=name, status="invalid_definition",
                score=0.0, issues=[f"tool '{name}' has no schema definition"],
            )
            verdicts.append(verdict)
            scores.append(verdict.score)
            aggregate_issues.extend(verdict.issues)
            continue

        if arg_error is not None:
            verdict = ToolCallVerdict(
                call_index=index, name=name, status="malformed",
                score=0.0, issues=[arg_error],
            )
            verdicts.append(verdict)
            scores.append(verdict.score)
            aggregate_issues.extend(verdict.issues)
            continue

        schema_score, schema_issues = validate_schema(args or {}, schema)
        status = "ok" if not schema_issues else "invalid_arguments"
        verdict = ToolCallVerdict(
            call_index=index, name=name, status=status, score=schema_score,
            issues=schema_issues,
        )
        verdicts.append(verdict)
        scores.append(verdict.score)
        if schema_issues:
            aggregate_issues.append(f"tool '{name}' call {index + 1}: " + ", ".join(schema_issues))

    base_score = sum(scores) / float(len(scores)) if scores else 0.0
    # Scale down the aggregate when unknown (hallucinated) tools are present.
    unknown = sum(1 for verdict in verdicts if verdict.status == "unknown_tool")
    confidence = max(0.0, min(1.0, base_score - 0.25 * unknown))

    recommendation = {"action": "proceed", "suggestions": []}
    if unknown:
        recommendation["action"] = "block"
        recommendation["suggestions"].append("Regenerate tool call: remove unknown/hallucinated tools")
    elif any(verdict.status == "invalid_arguments" for verdict in verdicts):
        recommendation["action"] = "fix"
        recommendation["suggestions"].append("Correct arguments against the declared tool schemas")
    elif any(verdict.status == "malformed" for verdict in verdicts):
        recommendation["action"] = "fix"
        recommendation["suggestions"].append("Emit arguments as a valid JSON object")

    return ToolCallResult(
        verdicts=verdicts,
        score=confidence,
        issues=aggregate_issues,
        recommendation=recommendation,
    )


def score_tool_calls(tool_calls: Sequence[Any], tools: Mapping[str, Mapping[str, Any]]) -> ToolCallResult:
    """Convenience wrapper accepting raw ``(name, arguments)`` pairs or dicts."""
    normalized = [_normalize_tool_call(raw) for raw in tool_calls]
    return check_tool_call(normalized, tools)


def _normalize_tool_call(raw: Any) -> ToolCall:
    if isinstance(raw, ToolCall):
        return raw
    if isinstance(raw, Mapping):
        name = _normalize_name(raw)
        arguments = raw.get("arguments")
        if arguments is None and isinstance(raw.get("function"), Mapping):
            arguments = raw["function"].get("arguments")
        return ToolCall(name=name, arguments=arguments)
    if isinstance(raw, (tuple, list)) and len(raw) == 2 and isinstance(raw[0], str):
        return ToolCall(name=raw[0], arguments=raw[1])
    raise TypeError("raw tool calls must be ToolCall, mapping, or (name, arguments) pairs")


def _unknown_tool_verdict(index: int, name: str, arg_error: Optional[str]) -> ToolCallVerdict:
    issues = [f"unknown or hallucinated tool name: '{name}'"]
    if arg_error is not None:
        issues.append(arg_error)
    return ToolCallVerdict(call_index=index, name=name, status="unknown_tool", score=0.0, issues=issues)