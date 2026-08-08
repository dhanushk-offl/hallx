"""Tests for claim-level grounding (hallx.attribution)."""

import asyncio

import pytest

from hallx.attribution import check_claim_grounding, check_claim_grounding_async, extract_claims
from hallx.types import Claim, ClaimGroundingResult


class Verifier:
    """Stub verifier whose output tracks hypothesis keywords."""

    def verify(self, premise: str, hypothesis: str) -> float:
        return 1.0 if "Paris" in hypothesis else 0.1

    async def averify(self, premise: str, hypothesis: str) -> float:
        return self.verify(premise, hypothesis)


def test_extract_claims_returns_typed_claims() -> None:
    claims = extract_claims("The sky is blue. Please note: birds fly.")

    assert all(isinstance(claim, Claim) for claim in claims)
    assert [claim.text for claim in claims] == ["The sky is blue.", "Please note: birds fly."]
    assert all(claim.status == "extracted" for claim in claims)
    assert claims[0].start < claims[0].end


def test_claim_grounding_skips_without_context() -> None:
    result = check_claim_grounding("The sky is blue.", [])

    assert isinstance(result, ClaimGroundingResult)
    assert result.score == pytest.approx(1.0)
    assert any("skipped" in issue for issue in result.issues)


def test_claim_grounding_with_stub_verifier() -> None:
    result = check_claim_grounding(
        "Paris is the capital of France. The moon is made of cheese.",
        context_docs=["The capital of France is Paris."],
        verifier=Verifier(),
    )

    assert result.supported_count == 1
    assert result.unsupported_count == 1
    by_text = {claim.text: claim.status for claim in result.claims}
    assert by_text["Paris is the capital of France."] == "supported"
    assert by_text["The moon is made of cheese."] == "unsupported"


def test_claim_grounding_async_with_stub_verifier() -> None:
    result = asyncio.run(
        check_claim_grounding_async(
            "Paris is the capital of France.",
            context_docs=["The capital of France is Paris."],
            verifier=Verifier(),
        )
    )

    assert result.supported_count == 1
    assert result.score == pytest.approx(1.0)


def test_claim_grounding_with_embeddings() -> None:
    def embed(text: str) -> list[float]:
        return [1.0, 0.0]

    result = check_claim_grounding(
        "Paris is the capital of France.",
        context_docs=["The capital of France is Paris."],
        embedding_callable=embed,
        context_embeddings=[[1.0, 0.1]],
    )

    assert result.unsupported_count == 0
    assert result.supported_count == 1


def test_claim_grounding_similarity_fallback() -> None:
    response = "The Eiffel Tower is located in Paris."
    result = check_claim_grounding(
        response,
        context_docs=["The Eiffel Tower is located in Paris, France."],
    )

    assert result.unsupported_count == 0
    assert result.supported_count == 1


def test_non_assertive_sentences_are_filtered() -> None:
    result = check_claim_grounding(
        "Please note that the sky is blue. Wow!",
        context_docs=["The sky is blue."],
    )

    filtered = [claim for claim in result.claims if claim.status == "filtered"]
    assert filtered == result.claims
    assert result.filtered_count == len(filtered)
    assert any("skipped" in issue or "filtered" in issue for issue in result.issues)