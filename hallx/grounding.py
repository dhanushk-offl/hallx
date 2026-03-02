"""Grounding and source-integrity checks."""

import inspect
import math
import re
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple

from rapidfuzz import fuzz

from hallx.types import Vector
from hallx.utils.text import normalize_text, split_sentences, to_context_blob


_FORBIDDEN_SOURCE_PATTERNS = [
    re.compile(r"\baccording to wikipedia\b", re.IGNORECASE),
    re.compile(r"\baccording to (?:a|an) study\b", re.IGNORECASE),
    re.compile(r"\bdoi:\s*10\.\d{4,9}/[-._;()/:a-z0-9]+\b", re.IGNORECASE),
]
_FAKE_URL_PATTERN = re.compile(r"https?://[^\s)]+", re.IGNORECASE)


SyncEmbeddingCallable = Callable[[str], Vector]


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


def detect_forbidden_sources(response: str, allow_web: bool = False) -> List[str]:
    """Detect ungrounded source references and suspicious URL patterns."""
    issues: List[str] = []
    if not response.strip():
        return issues

    for pattern in _FORBIDDEN_SOURCE_PATTERNS:
        if pattern.search(response):
            issues.append("potential fabricated or unverifiable citation detected")
            break

    urls = _FAKE_URL_PATTERN.findall(response)
    for url in urls:
        if not _looks_like_trusted_url(url) and not allow_web:
            issues.append(f"unverified external source mention detected: {url}")

    return issues


def check_grounding(
    response: str,
    context_docs: Iterable[str],
    embedding_callable: Optional[SyncEmbeddingCallable] = None,
    context_embeddings: Optional[Sequence[Sequence[float]]] = None,
    allow_web: bool = False,
) -> Tuple[float, List[str]]:
    """Compare response claims to context and return (score, issues)."""
    context_list = [doc for doc in context_docs if doc and doc.strip()]
    issues = detect_forbidden_sources(response, allow_web=allow_web)

    if not context_list:
        issues.append("grounding check skipped: no context provided")
        return 1.0, issues

    sentences = split_sentences(response)
    if not sentences:
        issues.append("grounding check failed: empty response")
        return 0.0, issues

    if embedding_callable is not None or context_embeddings is not None:
        score = _embedding_grounding_score(sentences, context_list, embedding_callable, context_embeddings)
    else:
        score = _fuzzy_grounding_score(sentences, context_list)

    weak_count = _count_weak_claims(sentences, context_list)
    if weak_count:
        issues.append(f"{weak_count} claim(s) appear weakly grounded against context")

    return score, issues


def _fuzzy_grounding_score(sentences: Sequence[str], context_list: Sequence[str]) -> float:
    context_blob = normalize_text(to_context_blob(context_list))
    sentence_scores: List[float] = []
    for sentence in sentences:
        ratio = float(fuzz.partial_ratio(normalize_text(sentence), context_blob)) / 100.0
        sentence_scores.append(ratio)
    return sum(sentence_scores) / float(len(sentence_scores))


def _embedding_grounding_score(
    sentences: Sequence[str],
    context_list: Sequence[str],
    embedding_callable: Optional[Callable[[str], Any]],
    context_embeddings: Optional[Sequence[Sequence[float]]],
) -> float:
    if context_embeddings is None:
        if embedding_callable is None:
            raise ValueError("embedding_callable is required when context_embeddings are not provided")
        context_embeddings = [_embed_sync(embedding_callable, doc) for doc in context_list]

    claim_embeddings: List[Sequence[float]] = []
    if embedding_callable is None:
        raise ValueError("embedding_callable is required for claim embeddings")

    for sentence in sentences:
        claim_embeddings.append(_embed_sync(embedding_callable, sentence))

    max_scores: List[float] = []
    for claim_vector in claim_embeddings:
        similarities = [_cosine_similarity(claim_vector, ctx_vector) for ctx_vector in context_embeddings]
        max_scores.append(max(similarities) if similarities else 0.0)
    return sum(max_scores) / float(len(max_scores))


def _count_weak_claims(sentences: Sequence[str], context_list: Sequence[str]) -> int:
    context_blob = normalize_text(to_context_blob(context_list))
    weak_count = 0
    for sentence in sentences:
        ratio = float(fuzz.partial_ratio(normalize_text(sentence), context_blob)) / 100.0
        if ratio < 0.4:
            weak_count += 1
    return weak_count


def _looks_like_trusted_url(url: str) -> bool:
    trusted_fragments = (
        ".gov",
        ".edu",
        "arxiv.org",
        "doi.org",
        "nature.com",
        "science.org",
    )
    return any(fragment in url.lower() for fragment in trusted_fragments)


def _embed_sync(embedding_callable: Callable[[str], Any], text: str) -> Sequence[float]:
    vector = embedding_callable(text)
    if inspect.isawaitable(vector):
        raise TypeError("sync embedding callable returned awaitable; use async API")
    if not isinstance(vector, Sequence):
        raise TypeError("embedding callable must return a numeric sequence")
    return [float(item) for item in vector]
