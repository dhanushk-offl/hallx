"""Schema-only validation flow."""

from hallx import Hallx


checker = Hallx()
report = checker.check_json(
    response={"answer": None, "extra": 1},
    schema={
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    },
)

print(report.score)
print(report.is_valid)
print(report.issues)
