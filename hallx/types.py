"""Typed models and protocols for hallx."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class LLMAdapter(Protocol):
    """Protocol for provider adapters consumed by Hallx."""

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text response synchronously."""

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text response asynchronously."""


@dataclass(frozen=True)
class HallxResult:
    """Represents hallucination-risk analysis output."""

    confidence: float
    risk_level: str
    scores: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendation: Dict[str, Any] = field(default_factory=dict)

    @property
    def breakdown(self) -> Dict[str, float]:
        """Backward-compatible alias for score breakdown."""
        return self.scores


@dataclass(frozen=True)
class SchemaValidationResult:
    """Structured schema validation report."""

    score: float
    issues: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Indicates whether any schema issues were detected."""
        return not self.issues


class HallxHighRiskError(RuntimeError):
    """Raised when strict mode detects high hallucination risk."""


class HallxAdapterError(RuntimeError):
    """Raised for adapter transport and response parsing failures."""


Vector = Sequence[float]
