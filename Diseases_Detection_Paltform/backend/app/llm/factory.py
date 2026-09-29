"""LLM Provider factory."""

from app.core.config import settings
from app.llm.base import ILLMProvider
from app.llm.gemma import GemmaLLMProvider
from app.llm.ollama import OllamaLLMProvider


class LLMFactory:
    """Factory creating LLM provider instances based on configuration."""

    @staticmethod
    def get_provider() -> ILLMProvider:
        provider_name = settings.LLM_PROVIDER.lower().strip()
        if provider_name in {"ollama", "local"}:
            return OllamaLLMProvider()
        if provider_name in {"gemma", "docker"}:
            return GemmaLLMProvider(base_url=settings.LLM_BASE_URL)
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
