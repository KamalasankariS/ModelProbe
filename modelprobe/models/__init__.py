"""Model adapters for querying LLMs.

Usage::

    from modelprobe.models import get_model

    model = get_model("ollama/llama3")
    response = model.generate("What is 2+2?")
    print(response.text)          # "4"
    print(response.latency_ms)    # 340.2
    print(response.token_count)   # 12

Supported providers:
    - ollama/<model>       — Local Ollama models (free)
    - openai/<model>       — OpenAI API (requires OPENAI_API_KEY)
    - anthropic/<model>    — Anthropic API (requires ANTHROPIC_API_KEY)
"""

from __future__ import annotations

from typing import Dict, Type

from modelprobe.models.base import ModelAdapter, ModelResponse
from modelprobe.models.ollama import OllamaAdapter
from modelprobe.models.openai import OpenAIAdapter
from modelprobe.models.anthropic import AnthropicAdapter

_PROVIDERS: Dict[str, Type[ModelAdapter]] = {
    "ollama": OllamaAdapter,
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
}


def get_model(model_string: str, **kwargs) -> ModelAdapter:
    """Parse a provider/model string and return an adapter.

    Args:
        model_string: Format "provider/model_name", e.g. "ollama/llama3".
                      If no provider prefix, defaults to "ollama".
        **kwargs: Extra config passed to the adapter (endpoint, api_key, etc.)

    Returns:
        An instantiated ModelAdapter ready to call .generate().
    """
    if "/" in model_string:
        provider, model_name = model_string.split("/", 1)
    else:
        provider = "ollama"
        model_name = model_string

    provider = provider.lower()
    cls = _PROVIDERS.get(provider)
    if cls is None:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Available: {', '.join(_PROVIDERS.keys())}"
        )
    return cls(model_name=model_name, **kwargs)


__all__ = [
    "get_model",
    "ModelAdapter",
    "ModelResponse",
    "OllamaAdapter",
    "OpenAIAdapter",
    "AnthropicAdapter",
]
