"""Text utility helpers."""

import re
from typing import Iterable, List, Tuple


_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")

_NON_ASSERTIVE_PREFIXES = (
    "hello",
    "hi ",
    "hey ",
    "thank",
    "thanks",
    "welcome",
    "regards",
    "sincerely",
    "cheers",
    "please note",
    "note that",
    "feel free",
    "if you have any questions",
    "let me know",
    "i think",
    "i believe",
    "i hope",
    "i'm not sure",
    "i am not sure",
    "it seems",
    "it looks like",
    "maybe",
    "perhaps",
    "hope this helps",
    "happy to help",
    "hope that helps",
    "this is a summary",
    "here is a summary",
    "here's a summary",
    "the answer is below",
    "here is your answer",
    "here's your answer",
    "please find",
    "attached",
)
_NON_ASSERTIVE_WHOLE = {
    "ok",
    "okay",
    "sure",
    "done",
    "got it",
    "no problem",
    "you're welcome",
    "you are welcome",
}


def split_sentences(text: str) -> List[str]:
    """Split text into normalized sentence-like segments."""
    if not text or not text.strip():
        return []
    return [part.strip() for part in _SENTENCE_SPLIT_PATTERN.split(text.strip()) if part.strip()]


def split_sentences_spans(text: str) -> List[Tuple[str, int, int]]:
    """Split text into ``(sentence, start, end)`` tuples with char offsets."""
    if not text or not text.strip():
        return []
    spans: List[Tuple[str, int, int]] = []
    cursor = 0
    for part in _SENTENCE_SPLIT_PATTERN.split(text.strip()):
        sentence = part.strip()
        if not sentence:
            continue
        start = text.index(sentence, cursor)
        end = start + len(sentence)
        spans.append((sentence, start, end))
        cursor = end
    return spans


def is_assertive_sentence(text: str) -> bool:
    """Return whether a sentence carries a factual claim (vs. filler/hedge)."""
    if not text or not text.strip():
        return False
    lowered = text.strip().lower()

    if lowered in _NON_ASSERTIVE_WHOLE:
        return False
    if len(lowered) < 8:
        return False

    if not re.search(r"[.!?]$", lowered):
        lowered = lowered.rstrip()

    for prefix in _NON_ASSERTIVE_PREFIXES:
        if lowered.startswith(prefix):
            return False

    if re.search(r"\b(i'll|i will|would you like|do you want|feel free to)\b", lowered):
        return False

    return True


def normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return " ".join(text.lower().strip().split())


def to_context_blob(context_docs: Iterable[str]) -> str:
    """Flatten context documents into one normalized blob."""
    normalized_docs = [normalize_text(doc) for doc in context_docs if doc and doc.strip()]
    return "\n".join(normalized_docs)
