"""Hugging Face Inference adapter."""

from typing import Any, Mapping, Optional

from hallx.adapters.base import HTTPAdapter
from hallx.types import HallxAdapterError


class HuggingFaceAdapter(HTTPAdapter):
    """Hugging Face text-generation inference adapter."""

    def __init__(
        self,
        model: str,
        api_key: str,
        timeout_seconds: float = 20.0,
        temperature: float = 0.0,
        max_tokens: int = 256,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.endpoint = f"https://api-inference.huggingface.co/models/{model}"
        super().__init__(
            model=model,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=extra_headers,
        )

    def _build_payload(self, prompt: str, system_prompt: Optional[str]) -> Mapping[str, Any]:
        merged_prompt = prompt if not system_prompt else f"System: {system_prompt}\nUser: {prompt}"
        return {
            "inputs": merged_prompt,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "return_full_text": False,
            },
        }

    def _parse_response(self, body: Mapping[str, Any]) -> str:
        if "error" in body:
            raise HallxAdapterError(f"HuggingFace API error: {body['error']}")
        text = body.get("generated_text")
        if isinstance(text, str):
            return text

        # Some endpoints return list payloads; keep compatibility in a lightweight way.
        raise HallxAdapterError("HuggingFace response missing generated_text")
