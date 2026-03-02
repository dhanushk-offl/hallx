"""Score aggregation and risk mapping."""

from typing import Dict, Mapping, Optional


DEFAULT_WEIGHTS: Dict[str, float] = {
    "schema": 0.34,
    "consistency": 0.33,
    "grounding": 0.33,
}

_REQUIRED_KEYS = tuple(DEFAULT_WEIGHTS.keys())


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def resolve_weights(weights: Optional[Mapping[str, float]]) -> Dict[str, float]:
    """Validate and normalize weight mapping."""
    if weights is None:
        return dict(DEFAULT_WEIGHTS)

    provided = dict(weights)
    if set(provided.keys()) != set(_REQUIRED_KEYS):
        raise ValueError(f"weights must contain exactly {_REQUIRED_KEYS}")

    total = sum(provided.values())
    if total <= 0.0:
        raise ValueError("weight sum must be > 0")
    if any(value < 0.0 for value in provided.values()):
        raise ValueError("weights must be non-negative")

    return {key: value / total for key, value in provided.items()}


def combine_scores(scores: Mapping[str, float], weights: Mapping[str, float]) -> float:
    """Compute weighted normalized confidence score."""
    missing = [key for key in _REQUIRED_KEYS if key not in scores]
    if missing:
        raise ValueError(f"missing score keys: {missing}")

    resolved = resolve_weights(weights)
    combined = sum(_clamp_score(float(scores[key])) * resolved[key] for key in _REQUIRED_KEYS)
    return _clamp_score(combined)


def risk_level_from_confidence(confidence: float) -> str:
    """Map confidence score to risk level."""
    value = _clamp_score(confidence)
    if value < 0.4:
        return "high"
    if value < 0.75:
        return "medium"
    return "low"
