"""Ollama provider for local model inference."""

from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import ILLMProvider


class OllamaLLMProvider(ILLMProvider):
    """Client for Ollama's native generate API."""

    provider_name = "Ollama"

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.provider_name = f"Ollama · {self.model}"
        # A cold CPU-only model can spend more than a minute loading before it
        # starts generating. Leave enough time for loading, prompt evaluation,
        # and a bounded JSON plan response.
        self.timeout = 420.0

    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        response, _used_model = await self.generate_response_with_status(prompt, context)
        return response

    async def generate_response_with_status(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, bool]:
        """Return model output and whether Ollama actually generated it."""
        del context  # The full schema-aware request is already included in the prompt.
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {"temperature": 0.1, "num_predict": 768},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                text = response.json().get("response", "")
                if isinstance(text, str) and text.strip():
                    return text, True
                logger.warning("Ollama returned an empty model response.")
        except Exception as error:
            logger.warning("Could not get a response from Ollama at %s: %s", endpoint, error)

        return (
            "The configured Ollama model did not return a response. No LLM plan update was produced.",
            False,
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return False
                models = response.json().get("models", [])
                return any(model.get("name", "").split(":")[0] == self.model.split(":")[0] for model in models)
        except Exception:
            return False
