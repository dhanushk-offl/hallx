"""Strict mode guardrail example."""

import hallx


checker = hallx.Hallx(strict=True)

try:
    checker.check(
        prompt="Return JSON",
        response={"unexpected": None},
        context=["Expected key is answer."],
        schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    )
except hallx.HallxHighRiskError as exc:
    print(f"blocked: {exc}")
    print("tip: retry with lower temperature, more context, and JSON mode")
