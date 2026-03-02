"""Retry strategy engine for production orchestration."""

from typing import Any, Dict, List, Mapping


def build_recommendation(
    confidence: float,
    risk_level: str,
    scores: Mapping[str, float],
    issues: List[str],
) -> Dict[str, Any]:
    """Build actionable recommendation from risk signals."""
    recommendation: Dict[str, Any] = {
        "action": "proceed",
        "suggested_temperature": 0.7,
        "suggestions": [],
    }

    if risk_level == "high":
        recommendation["action"] = "retry"
        recommendation["suggested_temperature"] = 0.2
    elif risk_level == "medium":
        recommendation["action"] = "retry"
        recommendation["suggested_temperature"] = 0.3

    suggestions: List[str] = []

    if scores.get("consistency", 1.0) < 0.7 or _has_issue(issues, "variance"):
        suggestions.append("Lower temperature")

    if scores.get("grounding", 1.0) < 0.7 or _has_issue(issues, "grounded"):
        suggestions.append("Increase context")

    if scores.get("schema", 1.0) < 0.95 or _schema_related_issue(issues):
        suggestions.append("Force JSON mode")

    if risk_level == "high" and confidence < 0.3:
        suggestions.append("Switch model")

    if not suggestions and recommendation["action"] == "retry":
        suggestions.append("Retry with lower temperature")

    recommendation["suggestions"] = suggestions
    return recommendation


def _has_issue(issues: List[str], keyword: str) -> bool:
    token = keyword.lower()
    return any(token in issue.lower() for issue in issues)


def _schema_related_issue(issues: List[str]) -> bool:
    markers = (
        "missing field",
        "wrong type",
        "enum violation",
        "unexpected extra field",
        "null injection",
    )
    lowered = [issue.lower() for issue in issues]
    return any(marker in issue for issue in lowered for marker in markers)
