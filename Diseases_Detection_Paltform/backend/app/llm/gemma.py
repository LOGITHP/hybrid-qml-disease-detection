"""Gemma LLM provider integration via internal Docker service."""

import os
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.llm.base import ILLMProvider


class GemmaLLMProvider(ILLMProvider):
    """Client for the dedicated containerized Gemma inference service."""

    provider_name = "Gemma"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "http://gemma:8001")
        self.timeout = 30.0

    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Call internal Gemma inference microservice."""
        response, _used_model = await self.generate_response_with_status(prompt, context)
        return response

    async def generate_response_with_status(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, bool]:
        """Return response text and whether it came from the live model endpoint."""
        endpoint = f"{self.base_url}/generate"
        payload = {"prompt": prompt, "context": context or {}}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(endpoint, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    response = data.get("text", "")
                    if isinstance(response, str) and response.strip():
                        return response, True
                logger.warning(f"Gemma service returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Could not reach Gemma service at {endpoint}: {str(e)}. Using fallback reasoning.")

        # Deterministic biomedical heuristic fallback if Gemma container is still starting
        return (
            "Recommended biomedical preprocessing workflow: "
            "1. Impute missing values with median for skewed clinical variables. "
            "2. Apply RobustScaler to preserve clinical outlier markers. "
            "3. Select top features via mutual information for optimal quantum state encoding.",
            False,
        )

    async def health_check(self) -> bool:
        """Check if Gemma service container is alive."""
        endpoint = f"{self.base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(endpoint)
                return resp.status_code == 200
        except Exception:
            return False
