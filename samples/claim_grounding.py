"""Claim-level grounding: which sentences in the response are supported?"""

from hallx import extract_claims
from hallx.attribution import check_claim_grounding, check_claim_grounding_async

response = (
    "The Eiffel Tower is in Paris. "
    "The Eiffel Tower is also in Berlin. "
    "Keep this note handy."
)

context = [
    "The Eiffel Tower is located in Paris, France.",
    "The Eiffel Tower was completed in 1889.",
]

# 1) Inspect extraction before scoring.
for claim in extract_claims(response):
    print(f"extracted [{claim.start}:{claim.end}] {claim.text!r}")

print("-" * 40)

# 2) Ground each claim against the best evidence snippet.
#    Pass LocalNLIChecker (hallx[nli]) or any FaithfulnessVerifier when installed.
result = check_claim_grounding(response, context)

print(f"score: {result.score:.2f}")
print(f"  supported: {result.supported_count}")
print(f"  weak:      {result.weak_count}")
print(f"  unsupported: {result.unsupported_count}")
for claim in result.claims:
    if claim.status != "filtered":
        print(f"  [{claim.status}] {claim.text}  sim={claim.similarity:.2f}")

print("-" * 40)

# 3. Async variant for embedding callables that are awaitable.
import asyncio


async def main():
    async_result = await check_claim_grounding_async(response, context)
    print(f"async score: {async_result.score:.2f}")


asyncio.run(main())