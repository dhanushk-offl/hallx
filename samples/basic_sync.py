"""Basic Hallx usage with schema + grounding."""

import hallx


checker = hallx.Hallx()

result = checker.check(
    prompt="Summarize the refund policy",
    response={"summary": "Refunds are allowed within 30 days."},
    context=["Refunds are allowed within 30 days of purchase."],
    schema={
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
        "additionalProperties": False,
    },
)

print(result.confidence)
print(result.risk_level)
print(result.scores)
print(result.issues)
print(result.recommendation)
