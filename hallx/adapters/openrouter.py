"""OpenRouter adapter."""

from typing import Any, Dict, List, Mapping, Optional

from hallx.adapters.base import HTTPAdapter
from hallx.types import HallxAdapterError


class OpenRouterAdapter(HTTPAdapter):
    """OpenRouter Chat Completions adapter."""

    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def _build_payload(self, prompt: str, system_prompt: Optional[str]) -> Mapping[str, Any]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _parse_response(self, body: Mapping[str, Any]) -> str:
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise HallxAdapterError("OpenRouter response missing choices")
        message = choices[0].get("message", {})
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise HallxAdapterError("OpenRouter response missing message content")
        return content
