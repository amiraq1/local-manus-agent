"""Ollama LLM Provider implementation."""
import json
from typing import AsyncGenerator

import httpx

from app.llm.base import LocalLLMProvider
from config import OLLAMA_CONFIG


class OllamaProvider(LocalLLMProvider):
    """LLM provider that connects to a local Ollama instance."""

    def __init__(self):
        self.base_url = OLLAMA_CONFIG["base_url"]
        self.model = OLLAMA_CONFIG["model"]
        self.temperature = OLLAMA_CONFIG["temperature"]
        self.max_tokens = OLLAMA_CONFIG["max_tokens"]

    async def generate(self, prompt: str) -> str:
        """Generate a complete response from Ollama.

        Args:
            prompt: The input prompt.

        Returns:
            Complete generated text.
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream response tokens from Ollama.

        Args:
            prompt: The input prompt.

        Yields:
            Individual tokens/chunks.
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done", False):
                            break

    def tool_call_parse(self, response: str) -> dict | None:
        """Parse a tool call from the LLM response.

        Looks for JSON tool call patterns in the response.

        Args:
            response: Raw LLM response text.

        Returns:
            Parsed tool call dict or None.
        """
        try:
            # Look for JSON object with tool and params
            text = response.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
                if "tool" in parsed and "params" in parsed:
                    return parsed
        except (json.JSONDecodeError, KeyError):
            pass
        return None
