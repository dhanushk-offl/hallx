"""Shared HTTP adapter primitives for LLM providers."""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional
from urllib import error, request

from hallx.types import HallxAdapterError


@dataclass(frozen=True)
class AdapterConfig:
    """Provider transport configuration."""

    model: str
    api_key: str
    timeout_seconds: float = 20.0


class HTTPAdapter:
    """Minimal secure HTTP JSON adapter with sync and async interfaces."""

    endpoint: str

    def __init__(
        self,
        model: str,
        api_key: str,
        timeout_seconds: float = 20.0,
        temperature: float = 0.0,
        max_tokens: int = 256,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        if not model.strip():
            raise ValueError("model must be non-empty")
        if not api_key.strip():
            raise ValueError("api_key must be non-empty")
        if timeout_seconds <= 0.0 or timeout_seconds > 120.0:
            raise ValueError("timeout_seconds must be between 0 and 120")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be > 0")

        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.temperature = max(0.0, min(2.0, temperature))
        self.max_tokens = max_tokens
        self.extra_headers = dict(extra_headers or {})

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text synchronously."""
        payload = self._build_payload(prompt=prompt, system_prompt=system_prompt)
        body = self._post_json(self.endpoint, payload, headers=self._headers())
        return self._parse_response(body)

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text asynchronously using a worker thread."""
        return await asyncio.to_thread(self.generate, prompt, system_prompt)

    @classmethod
    def from_env(cls, model: str, env_key_name: str, **kwargs: Any) -> "HTTPAdapter":
        """Construct adapter from environment variable key."""
        api_key = os.getenv(env_key_name, "")
        if not api_key:
            raise ValueError(f"missing environment variable: {env_key_name}")
        return cls(model=model, api_key=api_key, **kwargs)

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self.extra_headers)
        return headers

    def _build_payload(self, prompt: str, system_prompt: Optional[str]) -> Mapping[str, Any]:
        raise NotImplementedError

    def _parse_response(self, body: Mapping[str, Any]) -> str:
        raise NotImplementedError

    def _post_json(self, url: str, payload: Mapping[str, Any], headers: Mapping[str, str]) -> Dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        req = request.Request(url=url, data=data, headers=dict(headers), method="POST")

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
            raise HallxAdapterError(f"provider HTTP error {exc.code}: {message[:200]}") from exc
        except error.URLError as exc:
            raise HallxAdapterError(f"provider connection failed: {exc.reason}") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HallxAdapterError("provider returned non-JSON response") from exc

        if not isinstance(parsed, dict):
            raise HallxAdapterError("provider response must be a JSON object")
        return parsed
