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
    evidence: Optional["ClaimGroundingResult"] = None

    @property
    def breakdown(self) -> Dict[str, float]:
        """Backward-compatible alias for score breakdown."""
        return self.scores

    @property
    def claim_grounding_score(self) -> float:
        """Mean claim-level grounding score, or 0.0 when not evaluated."""
        if self.evidence is None:
            return 0.0
        return self.evidence.score

    @property
    def claims_supported(self) -> int:
        """Number of claims with supporting evidence."""
        if self.evidence is None:
            return 0
        return self.evidence.supported_count

    @property
    def unsupported_claims(self) -> List[str]:
        """Claim texts that have no supporting evidence in context."""
        if self.evidence is None:
            return []
        return [claim.text for claim in self.evidence.claims if claim.status == "unsupported"]


@dataclass(frozen=True)
class SchemaValidationResult:
    """Structured schema validation report."""

    score: float
    issues: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Indicates whether any schema issues were detected."""
        return not self.issues


@dataclass(frozen=True)
class Claim:
    """A sentence-level claim extracted from a response."""

    text: str
    start: int
    end: int
    status: str
    similarity: float = 0.0
    evidence_index: Optional[int] = None
    evidence_snippet: str = ""


@dataclass(frozen=True)
class ClaimGroundingResult:
    """Span-aware claim-level grounding report."""

    claims: List[Claim] = field(default_factory=list)
    score: float = 0.0
    supported_count: int = 0
    weak_count: int = 0
    unsupported_count: int = 0
    filtered_count: int = 0
    issues: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ToolCall:
    """A single tool invocation proposed by an LLM agent."""

    name: str
    arguments: Any = None
    raw_arguments: Optional[str] = None


@dataclass(frozen=True)
class ToolCallVerdict:
    """Per-call verdict for tool invocation validation."""

    call_index: int
    name: str
    status: str
    score: float
    issues: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ToolCallResult:
    """Aggregate tool-call validation report."""

    verdicts: List[ToolCallVerdict] = field(default_factory=list)
    score: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendation: Dict[str, Any] = field(default_factory=dict)


class HallxHighRiskError(RuntimeError):
    """Raised when strict mode detects high hallucination risk."""


class HallxAdapterError(RuntimeError):
    """Raised for adapter transport and response parsing failures."""


Vector = Sequence[float]
