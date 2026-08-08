"""Faithfulness verification protocol for pluggable claim->evidence scorers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class FaithfulnessVerifier(Protocol):
    """Scores whether ``hypothesis`` is entailed by ``premise``.

    Implementations should return a value in ``[0.0, 1.0]`` where higher means the
    hypothesis is more faithfully supported by the premise. Sync and async variants
    are both optional on the protocol; callers use whichever matches their flow.
    """

    def verify(self, premise: str, hypothesis: str) -> float:
        """Return faithfulness confidence for the hypothesis against the premise."""

    async def averify(self, premise: str, hypothesis: str) -> float:
        """Async variant of :meth:`verify`."""