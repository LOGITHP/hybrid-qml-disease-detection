"""LLM Provider factory."""

from app.core.config import settings
from app.llm.base import ILLMProvider
from app.llm.gemma import GemmaLLMProvider


class LLMFactory:
    """Factory creating LLM provider instances based on configuration."""

    @staticmethod
    def get_provider() -> ILLMProvider:
        provider_name = settings.LLM_PROVIDER.lower().strip()
        if provider_name in ["gemma", "local", "docker"]:
            return GemmaLLMProvider()
        return GemmaLLMProvider()
