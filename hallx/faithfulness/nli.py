"""Local NLI faithfulness backend (optional ``hallx[nli]`` extra).

Uses a cross-encoder NLI model via ``sentence-transformers`` to produce an
entailment-based faithfulness confidence. Heavy dependencies are imported
lazily so the core hallx install stays dependency-free.
"""

from typing import Any, Optional


class LocalNLIChecker:
    """Small local NLI verifier scoring ``premise entails hypothesis``.

    Example::

        from hallx.faithfulness import LocalNLIChecker

        verifier = LocalNLIChecker()
        score = verifier.verify(
            premise="The Eiffel Tower is in Paris, France.",
            hypothesis="The Eiffel Tower is in Paris.",
        )
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/nli-deberta-v3-v2",
        device: Optional[str] = None,
        max_length: int = 512,
    ) -> None:
        if not model_name.strip():
            raise ValueError("model_name must be non-empty")
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        self._model: Optional[Any] = None

    def verify(self, premise: str, hypothesis: str) -> float:
        """Return entailment confidence in ``[0, 1]``."""
        model = self._load()
        if not premise.strip():
            return 0.0
        if not hypothesis.strip():
            return 0.0

        scores = model.predict([(premise, hypothesis)])
        try:
            row = list(scores[0])
        except (TypeError, IndexError):
            row = list(scores)
        if len(row) < 3:
            # Non-triple NLI models expose a single similarity score.
            return float(max(0.0, min(1.0, row[0])))
        # Interpretation of (contradiction, neutral, entailment).
        entailment = max(0.0, min(1.0, float(row[2])))
        contradiction = max(0.0, min(1.0, float(row[0])))
        return max(0.0, min(1.0, entailment * (1.0 - contradiction)))

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "LocalNLIChecker requires the 'nli' extra: pip install 'hallx[nli]'"
            ) from exc

        kwargs = {"max_length": self.max_length}
        if self.device is not None:
            kwargs["device"] = self.device
        self._model = CrossEncoder(self.model_name, **kwargs)
        return self._model