"""Ollama adapter."""

from typing import Any, Dict, List, Mapping, Optional

from hallx.adapters.base import HTTPAdapter
from hallx.types import HallxAdapterError


class OllamaAdapter(HTTPAdapter):
    """Ollama chat adapter for local/server deployments."""

    def __init__(
        self,
        model: str,
        api_key: str = "ollama",
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 20.0,
        temperature: float = 0.0,
        max_tokens: int = 256,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.endpoint = f"{base_url.rstrip('/')}/api/chat"
        super().__init__(
            model=model,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=extra_headers,
        )

    def _headers(self) -> Dict[str, str]:
        # Ollama local deployments generally do not require bearer auth.
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self.extra_headers)
        return headers

    def _build_payload(self, prompt: str, system_prompt: Optional[str]) -> Mapping[str, Any]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

    def _parse_response(self, body: Mapping[str, Any]) -> str:
        if "error" in body:
            raise HallxAdapterError(f"Ollama API error: {body['error']}")

        message = body.get("message")
        if isinstance(message, Mapping):
            content = message.get("content")
            if isinstance(content, str):
                return content

        # Lightweight fallback compatibility with /api/generate-style shape.
        response = body.get("response")
        if isinstance(response, str):
            return response

        raise HallxAdapterError("Ollama response missing message content")
