"""hallx public API."""

from hallx.adapters import (
    AnthropicAdapter,
    GeminiAdapter,
    GrokAdapter,
    HuggingFaceAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
    PerplexityAdapter,
)
from hallx.attribution import check_claim_grounding, extract_claims
from hallx.calibration import FeedbackStore, default_feedback_db_path
from hallx.core import Hallx
from hallx.faithfulness import FaithfulnessVerifier, LocalNLIChecker
from hallx.toolcalls import check_tool_call, score_tool_calls
from hallx.types import (
    Claim,
    ClaimGroundingResult,
    HallxAdapterError,
    HallxHighRiskError,
    HallxResult,
    SchemaValidationResult,
    ToolCall,
    ToolCallResult,
    ToolCallVerdict,
)

__all__ = [
    "Hallx",
    "HallxResult",
    "SchemaValidationResult",
    "HallxHighRiskError",
    "HallxAdapterError",
    "FeedbackStore",
    "default_feedback_db_path",
    "Claim",
    "ClaimGroundingResult",
    "ToolCall",
    "ToolCallVerdict",
    "ToolCallResult",
    "check_tool_call",
    "score_tool_calls",
    "extract_claims",
    "FaithfulnessVerifier",
    "LocalNLIChecker",
    "OpenAIAdapter",
    "OpenRouterAdapter",
    "AnthropicAdapter",
    "PerplexityAdapter",
    "HuggingFaceAdapter",
    "OllamaAdapter",
    "GeminiAdapter",
    "GrokAdapter",
]
