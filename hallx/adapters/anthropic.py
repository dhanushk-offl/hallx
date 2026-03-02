"""Anthropic adapter."""

from typing import Any, Mapping, Optional

from hallx.adapters.base import HTTPAdapter
from hallx.types import HallxAdapterError


class AnthropicAdapter(HTTPAdapter):
    """Anthropic Messages API adapter."""

    endpoint = "https://api.anthropic.com/v1/messages"

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        headers["x-api-key"] = self.api_key
        headers["anthropic-version"] = "2023-06-01"
        headers.pop("Authorization", None)
        return headers

    def _build_payload(self, prompt: str, system_prompt: Optional[str]) -> Mapping[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
        return payload

    def _parse_response(self, body: Mapping[str, Any]) -> str:
        content = body.get("content")
        if not isinstance(content, list) or not content:
            raise HallxAdapterError("Anthropic response missing content")
        first = content[0]
        if not isinstance(first, Mapping):
            raise HallxAdapterError("Anthropic content is malformed")
        text = first.get("text")
        if not isinstance(text, str):
            raise HallxAdapterError("Anthropic content text missing")
        return text
