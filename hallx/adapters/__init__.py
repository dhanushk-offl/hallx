"""Provider adapters for plugging Hallx into common LLM APIs."""

from hallx.adapters.anthropic import AnthropicAdapter
from hallx.adapters.gemini import GeminiAdapter
from hallx.adapters.grok import GrokAdapter
from hallx.adapters.huggingface import HuggingFaceAdapter
from hallx.adapters.ollama import OllamaAdapter
from hallx.adapters.openai import OpenAIAdapter
from hallx.adapters.openrouter import OpenRouterAdapter
from hallx.adapters.perplexity import PerplexityAdapter

__all__ = [
    "OpenAIAdapter",
    "OpenRouterAdapter",
    "AnthropicAdapter",
    "PerplexityAdapter",
    "HuggingFaceAdapter",
    "OllamaAdapter",
    "GeminiAdapter",
    "GrokAdapter",
]
