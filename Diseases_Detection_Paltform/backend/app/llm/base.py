"""LLM Provider abstraction interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ILLMProvider(ABC):
    """Abstract interface for LLM inference providers (Gemma, Gemini, Local)."""

    @abstractmethod
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Submit prompt and context to the LLM and receive string response."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if LLM inference endpoint is reachable."""
        pass
