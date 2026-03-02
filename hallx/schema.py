"""Schema validation for structured LLM outputs."""

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from jsonschema import Draft7Validator

from hallx.types import SchemaValidationResult


Issue = str


_ERROR_TEMPLATES = {
    "required": "missing field: {detail}",
    "type": "wrong type at '{path}': expected {detail}",
    "additionalProperties": "unexpected extra field at '{path}': {detail}",
    "enum": "enum violation at '{path}': {detail}",
}


def _error_path(error_path: Sequence[Any]) -> str:
    return ".".join(str(part) for part in error_path) if error_path else "<root>"


def _format_issue(error: Any) -> str:
    path = _error_path(error.absolute_path)
    template = _ERROR_TEMPLATES.get(error.validator, "schema issue at '{path}': {detail}")
    detail = error.message
    return template.format(path=path, detail=detail)


def _schema_allows_null(schema: Optional[Mapping[str, Any]]) -> bool:
    if not schema:
        return True
    schema_type = schema.get("type")
    if schema_type == "null":
        return True
    if isinstance(schema_type, list) and "null" in schema_type:
        return True
    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        return any(_schema_allows_null(item) for item in any_of if isinstance(item, Mapping))
    return False


def _collect_null_injection_issues(
    response_obj: Any,
    schema: Optional[Mapping[str, Any]],
    path: str = "<root>",
) -> List[str]:
    issues: List[str] = []

    if response_obj is None and not _schema_allows_null(schema):
        issues.append(f"null injection at '{path}'")
        return issues

    if isinstance(response_obj, dict):
        properties = schema.get("properties", {}) if isinstance(schema, Mapping) else {}
        for key, value in response_obj.items():
            child_path = key if path == "<root>" else f"{path}.{key}"
            child_schema = properties.get(key) if isinstance(properties, Mapping) else None
            if isinstance(child_schema, Mapping):
                issues.extend(_collect_null_injection_issues(value, child_schema, child_path))
            elif value is None:
                issues.append(f"null injection at '{child_path}'")
        return issues

    if isinstance(response_obj, list):
        item_schema = schema.get("items") if isinstance(schema, Mapping) else None
        for idx, value in enumerate(response_obj):
            child_path = f"{path}[{idx}]"
            if isinstance(item_schema, Mapping):
                issues.extend(_collect_null_injection_issues(value, item_schema, child_path))
            elif value is None:
                issues.append(f"null injection at '{child_path}'")
    return issues


def validate_schema(response_obj: Any, schema: Mapping[str, Any]) -> Tuple[float, List[Issue]]:
    """Validate ``response_obj`` against JSON schema and return (score, issues)."""
    if not isinstance(schema, Mapping):
        raise TypeError("schema must be a mapping compatible with jsonschema")

    validator = Draft7Validator(dict(schema))
    errors = sorted(validator.iter_errors(response_obj), key=lambda item: list(item.path))
    issues = [_format_issue(error) for error in errors]
    issues.extend(_collect_null_injection_issues(response_obj, schema))

    if not issues:
        return 1.0, []

    # Smooth, bounded penalty per issue.
    score = max(0.0, 1.0 - min(1.0, 0.15 * len(issues)))
    return score, issues


def validate_schema_detailed(response_obj: Any, schema: Mapping[str, Any]) -> SchemaValidationResult:
    """Validate and return a typed schema report."""
    score, issues = validate_schema(response_obj, schema)
    return SchemaValidationResult(score=score, issues=issues)
