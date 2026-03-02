"""Consistency scoring via repeated generation comparisons."""

import inspect
import math
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple

from rapidfuzz import fuzz

from hallx.types import Vector


SyncLLMCallable = Callable[[str], str]
SyncEmbeddingCallable = Callable[[str], Vector]


def _text_similarity(a: str, b: str) -> float:
    return float(fuzz.ratio(a, b)) / 100.0


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding vectors must have identical dimensions")
    if not left:
        raise ValueError("embedding vectors must be non-empty")

    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_left * norm_right)))


def _pairwise_mean(values: List[Any], similarity: Callable[[Any, Any], float]) -> float:
    if len(values) < 2:
        return 1.0
    scores: List[float] = []
    for idx, left in enumerate(values):
        for right in values[idx + 1 :]:
            scores.append(similarity(left, right))
    if not scores:
        return 1.0
    return sum(scores) / float(len(scores))


def check_consistency(
    prompt: str,
    llm_callable: Optional[SyncLLMCallable],
    runs: int = 3,
    llm_kwargs: Optional[Mapping[str, Any]] = None,
    embedding_callable: Optional[SyncEmbeddingCallable] = None,
) -> Tuple[float, List[str]]:
    """Run sync callable multiple times and return (score, issues)."""
    if llm_callable is None:
        return 1.0, ["consistency check skipped: no llm callable provided"]

    if runs < 2:
        raise ValueError("runs must be >= 2 for consistency checking")

    kwargs = dict(llm_kwargs or {})
    outputs: List[str] = []

    for _ in range(runs):
        result = llm_callable(prompt, **kwargs)
        if inspect.isawaitable(result):
            raise TypeError("sync check received awaitable result; use check_consistency_async")
        if not isinstance(result, str):
            raise TypeError("llm callable must return str")
        outputs.append(result)

    if embedding_callable is not None:
        vectors = [_embed_sync(embedding_callable, text) for text in outputs]
        score = _pairwise_mean(vectors, _cosine_similarity)
    else:
        score = _pairwise_mean(outputs, _text_similarity)

    issues: List[str] = []
    variance = 1.0 - score
    if variance > 0.45:
        issues.append("high output variance detected across repeated generations")
    return score, issues


async def check_consistency_async(
    prompt: str,
    llm_callable: Optional[Callable[[str], Any]],
    runs: int = 3,
    llm_kwargs: Optional[Mapping[str, Any]] = None,
    embedding_callable: Optional[Callable[[str], Any]] = None,
) -> Tuple[float, List[str]]:
    """Run callable multiple times with async support and return (score, issues)."""
    if llm_callable is None:
        return 1.0, ["consistency check skipped: no llm callable provided"]

    if runs < 2:
        raise ValueError("runs must be >= 2 for consistency checking")

    kwargs = dict(llm_kwargs or {})
    outputs: List[str] = []

    for _ in range(runs):
        result = llm_callable(prompt, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, str):
            raise TypeError("llm callable must return str")
        outputs.append(result)

    if embedding_callable is not None:
        vectors = [await _embed_async(embedding_callable, text) for text in outputs]
        score = _pairwise_mean(vectors, _cosine_similarity)
    else:
        score = _pairwise_mean(outputs, _text_similarity)

    issues: List[str] = []
    variance = 1.0 - score
    if variance > 0.45:
        issues.append("high output variance detected across repeated generations")
    return score, issues


def _embed_sync(embedding_callable: SyncEmbeddingCallable, text: str) -> Sequence[float]:
    vector = embedding_callable(text)
    if inspect.isawaitable(vector):
        raise TypeError("sync embedding callable returned awaitable; use async check")
    if not isinstance(vector, Sequence):
        raise TypeError("embedding callable must return a numeric sequence")
    return [float(item) for item in vector]


async def _embed_async(embedding_callable: Callable[[str], Any], text: str) -> Sequence[float]:
    vector = embedding_callable(text)
    if inspect.isawaitable(vector):
        vector = await vector
    if not isinstance(vector, Sequence):
        raise TypeError("embedding callable must return a numeric sequence")
    return [float(item) for item in vector]
