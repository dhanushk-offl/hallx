"""Faithfulness verification protocol for pluggable claim->evidence scorers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class FaithfulnessVerifier(Protocol):
    """Scores whether ``hypothesis`` is entailed by ``premise``.

    Implementations should return a value in ``[0.0, 1.0]`` where higher means the
    hypothesis is more faithfully supported by the premise.

    Because this protocol is ``runtime_checkable``, ``isinstance(obj,
    FaithfulnessVerifier)`` only returns ``True`` when ``obj`` implements *both*
    ``verify`` and ``averify``. Callers that can accept sync-only backends use
    ``hasattr`` checks instead of ``isinstance``.
    """

    def verify(self, premise: str, hypothesis: str) -> float:
        """Return faithfulness confidence for the hypothesis against the premise."""

    async def averify(self, premise: str, hypothesis: str) -> float:
        """Async variant of :meth:`verify`."""