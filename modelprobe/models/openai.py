"""OpenAI-compatible model adapter."""

from __future__ import annotations

import os
import time

import httpx

from modelprobe.models.base import ModelAdapter, ModelResponse


class OpenAIAdapter(ModelAdapter):

    provider = "openai"

    def __init__(self, model_name: str, api_key: str | None = None, endpoint: str | None = None, **kwargs):
        super().__init__(model_name)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.endpoint = (endpoint or "https://api.openai.com/v1/chat/completions").rstrip("/")

    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key=.")

        start = time.perf_counter()
        resp = httpx.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                **kwargs,
            },
            timeout=60.0,
        )
        latency = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()

        choice = data.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "").strip()
        usage = data.get("usage", {})
        token_count = usage.get("total_tokens")

        return ModelResponse(
            text=text,
            latency_ms=round(latency, 2),
            token_count=token_count,
            model=self.model_name,
            provider=self.provider,
        )
