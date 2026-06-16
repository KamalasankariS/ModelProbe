"""Ollama model adapter for local LLM inference."""

from __future__ import annotations

import time

import httpx

from modelprobe.models.base import ModelAdapter, ModelResponse


class OllamaAdapter(ModelAdapter):

    provider = "ollama"

    def __init__(self, model_name: str, endpoint: str = "http://localhost:11434", **kwargs):
        super().__init__(model_name)
        self.endpoint = endpoint.rstrip("/")

    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        url = f"{self.endpoint}/api/generate"
        start = time.perf_counter()
        resp = httpx.post(
            url,
            json={"model": self.model_name, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        latency = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()

        return ModelResponse(
            text=data.get("response", "").strip(),
            latency_ms=round(latency, 2),
            token_count=data.get("eval_count"),
            model=self.model_name,
            provider=self.provider,
        )
