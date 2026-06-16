"""Base classes for model adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelResponse:
    """Standardized response from any model adapter."""

    text: str
    latency_ms: float
    token_count: Optional[int] = None
    model: str = ""
    provider: str = ""


class ModelAdapter(ABC):
    """Base class all model adapters must implement."""

    provider: str = ""

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Send a prompt to the model and return a standardized response."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name!r})"
