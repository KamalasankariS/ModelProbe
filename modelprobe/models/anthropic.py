"""Anthropic model adapter."""

from __future__ import annotations

import os
import time

import httpx

from modelprobe.models.base import ModelAdapter, ModelResponse


class AnthropicAdapter(ModelAdapter):

    provider = "anthropic"

    def __init__(self, model_name: str, api_key: str | None = None, **kwargs):
        super().__init__(model_name)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY or pass api_key=.")

        start = time.perf_counter()
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "max_tokens": kwargs.get("max_tokens", 1024),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60.0,
        )
        latency = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()

        blocks = data.get("content", [])
        text = " ".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
        usage = data.get("usage", {})
        token_count = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        return ModelResponse(
            text=text,
            latency_ms=round(latency, 2),
            token_count=token_count or None,
            model=self.model_name,
            provider=self.provider,
        )
