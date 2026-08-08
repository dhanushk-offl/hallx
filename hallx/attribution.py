"""Claim-level grounding attribution with span-aware evidence reporting."""

import inspect
import math
from typing import Any, Callable, List, Optional, Sequence, Tuple

from rapidfuzz import fuzz

from hallx.faithfulness.base import FaithfulnessVerifier
from hallx.grounding import detect_forbidden_sources
from hallx.types import Claim, ClaimGroundingResult
from hallx.utils.text import is_assertive_sentence, normalize_text, split_sentences_spans


ClaimSpan = Tuple[str, int, int]

TextField = Callable[[str], Any]

_SUPPORTED_THRESHOLD = 0.7
_WEAK_THRESHOLD = 0.4


def extract_claims(response: str) -> List[Claim]:
    """Split a response into sentence-level ``Claim`` objects with offsets."""
    return [
        Claim(text=text, start=start, end=end, status="extracted")
        for text, start, end in _sentence_spans(response)
    ]


def _sentence_spans(response: str) -> List[ClaimSpan]:
    return split_sentences_spans(response)


def check_claim_grounding(
    response: str,
    context_docs: Sequence[str],
    embedding_callable: Optional[TextField] = None,
    context_embeddings: Optional[Sequence[Sequence[float]]] = None,
    supported_threshold: float = _SUPPORTED_THRESHOLD,
    weak_threshold: float = _WEAK_THRESHOLD,
    allow_web: bool = False,
    verifier: Optional[FaithfulnessVerifier] = None,
) -> ClaimGroundingResult:
    """Score each claim against the best evidence snippet and return a report."""
    issues: List[str] = detect_forbidden_sources(response, allow_web=allow_web)

    context_list = [doc for doc in context_docs if doc and doc.strip()]
    if not context_list:
        issues.append("claim grounding skipped: no context provided")
        return _empty_report(issues=issues)

    spans = _sentence_spans(response)
    if not spans:
        issues.append("claim grounding failed: empty response")
        return ClaimGroundingResult(claims=[], score=0.0, issues=issues)

    context_embeddings = _resolve_context_embeddings(
        context_list, context_embeddings, embedding_callable
    )
    claims: List[Claim] = []
    similarities: List[float] = []

    for text, start, end in spans:
        if not is_assertive_sentence(text):
            claims.append(Claim(text=text, start=start, end=end, status="filtered"))
            continue

        similarity, evidence_index = _best_evidence(
            text=text,
            context_list=context_list,
            context_embeddings=context_embeddings,
            embedding_callable=embedding_callable,
            verifier=verifier,
        )
        status = _filter_from_similarity(
            similarity, supported_threshold=supported_threshold, weak_threshold=weak_threshold
        )
        claims.append(
            Claim(
                text=text,
                start=start,
                end=end,
                status=status,
                similarity=similarity,
                evidence_index=evidence_index,
                evidence_snippet=_snippet(context_list[evidence_index]),
            )
        )
        similarities.append(similarity)

    assertive = [claim for claim in claims if claim.status != "filtered"]
    if not assertive:
        issues.append("claim grounding skipped: no assertive claims detected")
        return _empty_report(issues=issues, claims=claims)

    score = sum(similarities) / float(len(similarities))

    unsupported = [claim for claim in assertive if claim.status == "unsupported"]
    weak = [claim for claim in assertive if claim.status == "weak"]
    if weak:
        issues.append(f"{len(weak)} claim(s) are weakly grounded against context")
    if unsupported:
        issues.append(f"{len(unsupported)} claim(s) have no supporting evidence in context")
    if any(claim.status == "filtered" for claim in claims):
        filtered = sum(1 for claim in claims if claim.status == "filtered")
        issues.append(f"{filtered} non-factual filler sentence(s) filtered from grounding")

    return ClaimGroundingResult(
        claims=claims,
        score=score,
        supported_count=sum(1 for claim in assertive if claim.status == "supported"),
        weak_count=len(weak),
        unsupported_count=len(unsupported),
        filtered_count=sum(1 for claim in claims if claim.status == "filtered"),
        issues=issues,
    )


async def check_claim_grounding_async(
    response: str,
    context_docs: Sequence[str],
    embedding_callable: Optional[TextField] = None,
    context_embeddings: Optional[Sequence[Sequence[float]]] = None,
    supported_threshold: float = _SUPPORTED_THRESHOLD,
    weak_threshold: float = _WEAK_THRESHOLD,
    allow_web: bool = False,
    verifier: Optional[FaithfulnessVerifier] = None,
) -> ClaimGroundingResult:
    """Async variant supporting sync or async embedding callables."""
    issues: List[str] = detect_forbidden_sources(response, allow_web=allow_web)

    context_list = [doc for doc in context_docs if doc and doc.strip()]
    if not context_list:
        issues.append("claim grounding skipped: no context provided")
        return _empty_report(issues=issues)

    spans = _sentence_spans(response)
    if not spans:
        issues.append("claim grounding failed: empty response")
        return ClaimGroundingResult(claims=[], score=0.0, issues=issues)

    context_embeddings = await _resolve_context_embeddings_async(
        context_list, context_embeddings, embedding_callable
    )
    claims: List[Claim] = []
    similarities: List[float] = []

    for text, start, end in spans:
        if not is_assertive_sentence(text):
            claims.append(Claim(text=text, start=start, end=end, status="filtered"))
            continue
        similarity, best_index = await _best_evidence_async(
            text=text,
            context_list=context_list,
            context_embeddings=context_embeddings,
            embedding_callable=embedding_callable,
            verifier=verifier,
        )
        status = _filter_from_similarity(
            similarity, supported_threshold=supported_threshold, weak_threshold=weak_threshold
        )
        claims.append(
            Claim(
                text=text,
                start=start,
                end=end,
                status=status,
                similarity=similarity,
                evidence_index=best_index,
                evidence_snippet=_snippet(context_list[best_index]),
            )
        )
        similarities.append(similarity)

    assertive = [claim for claim in claims if claim.status != "filtered"]
    if not assertive:
        issues.append("claim grounding skipped: no assertive claims detected")
        return _empty_report(issues=issues, claims=claims)

    score = sum(similarities) / float(len(similarities))

    weak = [claim for claim in assertive if claim.status == "weak"]
    unsupported = [claim for claim in assertive if claim.status == "unsupported"]
    if weak:
        issues.append(f"{len(weak)} claim(s) are weakly grounded against context")
    if unsupported:
        issues.append(f"{len(unsupported)} claim(s) have no supporting evidence in context")
    if any(claim.status == "filtered" for claim in claims):
        filtered = sum(1 for claim in claims if claim.status == "filtered")
        issues.append(f"{filtered} non-claim filler sentence(s) filtered from scoring")

    return ClaimGroundingResult(
        claims=claims,
        score=score,
        supported_count=sum(1 for claim in assertive if claim.status == "supported"),
        weak_count=len(weak),
        unsupported_count=len(unsupported),
        filtered_count=sum(1 for claim in claims if claim.status == "filtered"),
        issues=issues,
    )


def _empty_report(
    *,
    issues: List[str],
    claims: Optional[List[Claim]] = None,
) -> ClaimGroundingResult:
    return ClaimGroundingResult(
        claims=claims or [],
        score=1.0,
        issues=issues,
    )


def _resolve_context_embeddings(
    context_list: Sequence[str],
    context_embeddings: Optional[Sequence[Sequence[float]]],
    embedding_callable: Optional[TextField],
) -> Optional[List[Sequence[float]]]:
    if context_embeddings is not None:
        normalized = []
        for vector in context_embeddings:
            if vector is None:
                return None
            normalized.append(list(vector))
        return normalized
    if embedding_callable is None:
        return None
    return [_embed_sync(embedding_callable, doc) for doc in context_list]


async def _resolve_context_embeddings_async(
    context_list: Sequence[str],
    context_embeddings: Optional[Sequence[Sequence[float]]],
    embedding_callable: Optional[TextField],
) -> Optional[List[Sequence[float]]]:
    if context_embeddings is not None:
        normalized = []
        for vector in context_embeddings:
            if vector is None:
                return None
            normalized.append(list(vector))
        return normalized
    if embedding_callable is None:
        return None
    return [await _embed_async(embedding_callable, doc) for doc in context_list]


def _best_evidence(
    text: str,
    context_list: Sequence[str],
    context_embeddings: Optional[Sequence[Sequence[float]]],
    embedding_callable: Optional[TextField],
    verifier: Optional[FaithfulnessVerifier] = None,
) -> Tuple[float, int]:
    if verifier is not None and hasattr(verifier, "verify"):
        scores = [max(0.0, min(1.0, float(verifier.verify(doc, text)))) for doc in context_list]
    elif context_embeddings is not None and embedding_callable is not None:
        claim_vector = _embed_sync(embedding_callable, text)
        scores = [
            _cosine_similarity(claim_vector, ctx) for ctx in context_embeddings
        ]
    else:
        claim_norm = normalize_text(text)
        scores = [
            float(fuzz.partial_ratio(claim_norm, normalize_text(doc))) / 100.0
            for doc in context_list
        ]
    best_index = int(max(range(len(scores)), key=lambda idx: scores[idx]))
    return max(0.0, min(1.0, scores[best_index])), best_index


async def _best_evidence_async(
    text: str,
    context_list: Sequence[str],
    context_embeddings: Optional[Sequence[Sequence[float]]],
    embedding_callable: Optional[TextField],
    verifier: Optional[FaithfulnessVerifier] = None,
) -> Tuple[float, int]:
    if verifier is not None and hasattr(verifier, "averify"):
        scores: List[float] = []
        for doc in context_list:
            value = verifier.averify(doc, text)
            if inspect.isawaitable(value):
                value = await value
            scores.append(max(0.0, min(1.0, float(value))))
    elif verifier is not None and hasattr(verifier, "verify"):
        scores = [max(0.0, min(1.0, float(verifier.verify(doc, text)))) for doc in context_list]
    elif context_embeddings is not None and embedding_callable is not None:
        claim_vector = await _embed_async(embedding_callable, text)
        scores = [
            _cosine_similarity(claim_vector, ctx) for ctx in context_embeddings
        ]
    else:
        best_norm = normalize_text(text)
        scores = [
            float(fuzz.partial_ratio(best_norm, normalize_text(doc))) / 100.0
            for doc in context_list
        ]
    best_index = int(max(range(len(scores)), key=lambda idx: scores[idx]))
    return max(0.0, min(1.0, scores[best_index])), best_index


def _filter_from_similarity(
    similarity: float,
    *,
    supported_threshold: float,
    weak_threshold: float,
) -> str:
    if similarity >= supported_threshold:
        return "supported"
    if similarity >= weak_threshold:
        return "weak"
    return "unsupported"


def _snippet(doc: str, limit: int = 240) -> str:
    return doc[:limit]


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


def _embed_sync(embedding_callable: TextField, text: str) -> Sequence[float]:
    vector = embedding_callable(text)
    if inspect.isawaitable(vector):
        raise TypeError("sync embedding callable returned awaitable; use async API")
    if not isinstance(vector, Sequence):
        raise TypeError("embedding callable must return a numeric sequence")
    return [float(item) for item in vector]


async def _embed_async(embedding_callable: TextField, text: str) -> Sequence[float]:
    vector = embedding_callable(text)
    if inspect.isawaitable(vector):
        vector = await vector
    if not isinstance(vector, Sequence):
        raise TypeError("embedding callable must return a numeric sequence")
    return [float(item) for item in vector]