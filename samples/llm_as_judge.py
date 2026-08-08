"""LLM-as-judge groundness: reuse a Hallx adapter as a faithfulness verifier."""

import asyncio
from typing import Optional

from hallx import Hallx
from hallx.judge import GroundingJudge
from hallx.types import LLMAdapter


class ExampleAdapter:
    """A stand-in provider adapter that returns score-like text.

    In real code, use hallx.OpenAIAdapter("gpt-4o-mini", api_key=...),
    AnthropicAdapter, OpenRouterAdapter, etc.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "92"

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "92"


# GroundingJudge follows the FaithfulnessVerifier protocol, so it plugs
# straight into Hallx.check(claims=True, verifier=judge).
adapter: LLMAdapter = ExampleAdapter()
judge = GroundingJudge(llm_adapter=adapter)

checker = Hallx(profile="balanced")

result = checker.check(
    prompt="Summarize the refund policy",
    response="Refunds are allowed within 30 days.",
    context=["Refunds are allowed within 30 days of purchase."],
    claims=True,
    verifier=judge,
)

print("confident:", round(result.confidence, 3))
print("claim_grounding:", round(result.claim_grounding_score, 3))
print("claims_supported:", result.claims_supported)
print("unsupported:", result.unsupported_claims)

# The judge is also usable directly and asynchronously.
print("judge:", judge.verify("evidence", "claim"))
print("judge async:", asyncio.run(judge.averify("evidence", "claim")))