"""Provider adapter matrix for quick integration checks.

Set provider API keys in environment variables before running.
"""

import os

from hallx.adapters import (
    AnthropicAdapter,
    GeminiAdapter,
    GrokAdapter,
    HuggingFaceAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
    PerplexityAdapter,
)


def build_adapters() -> dict[str, object]:
    adapters: dict[str, object] = {}

    if os.getenv("OPENAI_API_KEY"):
        adapters["openai"] = OpenAIAdapter("gpt-4.1-mini", os.environ["OPENAI_API_KEY"])
    if os.getenv("OPENROUTER_API_KEY"):
        adapters["openrouter"] = OpenRouterAdapter(
            "openai/gpt-4o-mini", os.environ["OPENROUTER_API_KEY"]
        )
    if os.getenv("ANTHROPIC_API_KEY"):
        adapters["anthropic"] = AnthropicAdapter(
            "claude-3-5-sonnet-latest", os.environ["ANTHROPIC_API_KEY"]
        )
    if os.getenv("PERPLEXITY_API_KEY"):
        adapters["perplexity"] = PerplexityAdapter(
            "sonar", os.environ["PERPLEXITY_API_KEY"]
        )
    if os.getenv("HF_API_KEY"):
        adapters["huggingface"] = HuggingFaceAdapter(
            "gpt2", os.environ["HF_API_KEY"]
        )
    if os.getenv("GEMINI_API_KEY"):
        adapters["gemini"] = GeminiAdapter("gemini-1.5-flash", os.environ["GEMINI_API_KEY"])
    if os.getenv("XAI_API_KEY"):
        adapters["grok"] = GrokAdapter("grok-2", os.environ["XAI_API_KEY"])
    if os.getenv("OLLAMA_BASE_URL"):
        adapters["ollama"] = OllamaAdapter(
            model="llama3.1",
            base_url=os.environ["OLLAMA_BASE_URL"],
        )

    return adapters


if __name__ == "__main__":
    for name, adapter in build_adapters().items():
        print(name, type(adapter).__name__)
