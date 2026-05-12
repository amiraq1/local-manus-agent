"""Base LLM Provider interface and factory."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LocalLLMProvider(ABC):
    """Abstract base class for local LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a complete response for the given prompt.

        Args:
            prompt: The input prompt.

        Returns:
            Complete generated text.
        """
        ...

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream response tokens for the given prompt.

        Args:
            prompt: The input prompt.

        Yields:
            Individual tokens/chunks of the response.
        """
        ...

    @abstractmethod
    def tool_call_parse(self, response: str) -> dict | None:
        """Parse a tool call from the LLM response.

        Args:
            response: Raw LLM response text.

        Returns:
            Parsed tool call dict or None if no tool call found.
        """
        ...


_provider_instance: LocalLLMProvider | None = None


def get_llm_provider() -> LocalLLMProvider:
    """Get the configured LLM provider instance (singleton).

    Returns:
        The active LocalLLMProvider instance.
    """
    global _provider_instance
    if _provider_instance is None:
        from config import LLM_PROVIDER
        if LLM_PROVIDER == "ollama":
            from app.llm.ollama_provider import OllamaProvider
            _provider_instance = OllamaProvider()
        elif LLM_PROVIDER == "litert":
            from app.llm.litert_provider import LiteRTProvider
            _provider_instance = LiteRTProvider()
        else:
            raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
    return _provider_instance
