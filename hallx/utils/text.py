"""Text utility helpers."""

import re
from typing import Iterable, List


_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> List[str]:
    """Split text into normalized sentence-like segments."""
    if not text or not text.strip():
        return []
    return [part.strip() for part in _SENTENCE_SPLIT_PATTERN.split(text.strip()) if part.strip()]


def normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return " ".join(text.lower().strip().split())


def to_context_blob(context_docs: Iterable[str]) -> str:
    """Flatten context documents into one normalized blob."""
    normalized_docs = [normalize_text(doc) for doc in context_docs if doc and doc.strip()]
    return "\n".join(normalized_docs)
