"""Retry strategy middleware example."""

from hallx import Hallx


checker = Hallx()

outputs = ["answer A", "answer C", "answer B"]


def unstable_llm(_: str) -> str:
    return outputs.pop(0)


result = checker.check(
    prompt="Return one-line answer",
    response="According to Wikipedia, uncertain answer.",
    context=["Internal source says: answer A."],
    llm_callable=unstable_llm,
    consistency_runs=3,
)

print(result.confidence)
print(result.risk_level)
print(result.recommendation)

if result.recommendation.get("action") == "retry":
    print("Retry with:", result.recommendation)
