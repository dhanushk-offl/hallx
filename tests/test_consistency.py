import pytest

from hallx.consistency import check_consistency, check_consistency_async


def test_consistency_sync_high_score_for_same_output() -> None:
    def stable_llm(_: str) -> str:
        return "Paris is the capital of France."

    score, issues = check_consistency("capital?", stable_llm, runs=3)

    assert score == pytest.approx(1.0)
    assert issues == []


def test_consistency_sync_skip_without_callable() -> None:
    score, issues = check_consistency("prompt", None, runs=3)

    assert score == 1.0
    assert any("skipped" in issue for issue in issues)


@pytest.mark.asyncio
async def test_consistency_async_with_variable_outputs() -> None:
    outputs = ["A", "B", "A"]

    async def noisy_llm(_: str) -> str:
        return outputs.pop(0)

    score, issues = await check_consistency_async("prompt", noisy_llm, runs=3)

    assert 0.0 <= score < 1.0
    assert any("variance" in issue for issue in issues)


def test_consistency_with_embedding_callable() -> None:
    outputs = ["alpha", "alpha", "alpha"]

    def stable_llm(_: str) -> str:
        return outputs.pop(0)

    def embedding(text: str) -> list[float]:
        return [float(len(text)), 1.0]

    score, issues = check_consistency(
        prompt="x",
        llm_callable=stable_llm,
        runs=3,
        embedding_callable=embedding,
    )

    assert score == pytest.approx(1.0)
    assert issues == []
