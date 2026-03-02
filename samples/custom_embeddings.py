"""Grounding and consistency with a user-provided embedding callable."""

from hallx import Hallx


def tiny_embedding(text: str) -> list[float]:
    # Placeholder deterministic embedding for demonstration/testing.
    vowels = sum(1 for c in text.lower() if c in "aeiou")
    return [float(len(text)), float(vowels), float(len(set(text.lower())))]


checker = Hallx()
result = checker.check(
    prompt="What is Hallx?",
    response="Hallx scores hallucination risk in model outputs.",
    context=["Hallx is a lightweight confidence scoring engine for LLM outputs."],
    llm_callable=lambda _: "Hallx scores hallucination risk in model outputs.",
    consistency_runs=3,
    embedding_callable=tiny_embedding,
)

print(result.scores)
print(result.confidence)
