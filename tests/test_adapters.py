import json
from typing import Any
from unittest.mock import patch

import pytest

from hallx.adapters import (
    AnthropicAdapter,
    GeminiAdapter,
    GrokAdapter,
    HuggingFaceAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
    PerplexityAdapter,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def test_openai_adapter_generate_with_mocked_transport() -> None:
    adapter = OpenAIAdapter(model="gpt-test", api_key="key")

    with patch("urllib.request.urlopen", return_value=_FakeResponse({"choices": [{"message": {"content": "ok"}}]})):
        text = adapter.generate("hello")

    assert text == "ok"


@pytest.mark.parametrize(
    "adapter,response",
    [
        (OpenRouterAdapter("m", "k"), {"choices": [{"message": {"content": "a"}}]}),
        (PerplexityAdapter("m", "k"), {"choices": [{"message": {"content": "b"}}]}),
        (GrokAdapter("m", "k"), {"choices": [{"message": {"content": "c"}}]}),
        (AnthropicAdapter("m", "k"), {"content": [{"text": "d"}]}),
        (GeminiAdapter("gemini-1.5-flash", "k"), {"candidates": [{"content": {"parts": [{"text": "e"}]}}]}),
        (HuggingFaceAdapter("gpt2", "k"), {"generated_text": "f"}),
    ],
)
def test_provider_parse_contracts(adapter: object, response: dict[str, Any]) -> None:
    text = adapter._parse_response(response)  # type: ignore[attr-defined]
    assert isinstance(text, str)
    assert text
