"""Google Gemini adapter."""

from typing import Any, Mapping, Optional

from hallx.adapters.base import HTTPAdapter
from hallx.types import HallxAdapterError


class GeminiAdapter(HTTPAdapter):
    """Google Gemini generateContent adapter."""

    def __init__(
        self,
        model: str,
        api_key: str,
        timeout_seconds: float = 20.0,
        temperature: float = 0.0,
        max_tokens: int = 256,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            f"?key={api_key}"
        )
        self.endpoint = endpoint
        super().__init__(
            model=model,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=extra_headers,
        )

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        headers.pop("Authorization", None)
        return headers

    def _build_payload(self, prompt: str, system_prompt: Optional[str]) -> Mapping[str, Any]:
        user_text = prompt if not system_prompt else f"System: {system_prompt}\nUser: {prompt}"
        return {
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
            "contents": [{"parts": [{"text": user_text}]}],
        }

    def _parse_response(self, body: Mapping[str, Any]) -> str:
        candidates = body.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise HallxAdapterError("Gemini response missing candidates")
        first = candidates[0]
        if not isinstance(first, Mapping):
            raise HallxAdapterError("Gemini candidate is malformed")
        content = first.get("content")
        if not isinstance(content, Mapping):
            raise HallxAdapterError("Gemini response missing content")
        parts = content.get("parts")
        if not isinstance(parts, list) or not parts:
            raise HallxAdapterError("Gemini content missing parts")
        part0 = parts[0]
        if not isinstance(part0, Mapping):
            raise HallxAdapterError("Gemini part is malformed")
        text = part0.get("text")
        if not isinstance(text, str):
            raise HallxAdapterError("Gemini content text missing")
        return text
