"""Tool-call validation for agentic flows.

Guards against hallucinated tool names and malformed arguments before an
agentic tool call is executed downstream.
"""

from hallx import Hallx

# Declared tool schemas the agent is allowed to invoke.
tools = {
    "get_weather": {
        "type": "object",
        "properties": {"city": {"type": "string"}, "unit": {"type": "string", "enum": ["c", "f"]}},
        "required": ["city"],
        "additionalProperties": False,
    },
    "send_email": {
        "parameters": {
            "type": "object",
            "properties": {"to": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to"],
        }
    },
}

checker = Hallx()

# Raw (name, arguments) pairs, OpenAI-style dicts, or ToolCall objects all work.
agent_response = [
    {"function": {"name": "get_weather", "arguments": '{"city": "Paris"}'}},
    {"name": "delete_server", "arguments": "{}"},  # hallucinated tool name
]

result = checker.check_tool_call(agent_response, tools)

print("score:", result.score)
for verdict in result.verdicts:
    print(f"  {verdict.status}: '{verdict.name}' -> {verdict.issues or 'ok'}")

print("action:", result.recommendation["action"])
if result.recommendation["action"] == "block":
    print("TIP: regenerate the tool call without unknown tools before executing.")