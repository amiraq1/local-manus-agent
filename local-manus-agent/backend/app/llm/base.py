"""Base LLM Provider interface and factory accessor."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LocalLLMProvider(ABC):
    """Abstract base class for local LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a complete response."""
        ...

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response tokens."""
        ...

    @abstractmethod
    def tool_call_parse(self, response: str) -> dict | None:
        """Parse a tool call from the LLM response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is ready to use."""
        ...

    @abstractmethod
    def model_info(self) -> dict:
        """Return info about the current model/provider."""
        ...


def get_llm_provider() -> LocalLLMProvider:
    """Get the configured LLM provider (delegates to factory).

    This function exists for backward compatibility.
    """
    from app.llm.factory import get_llm_provider as _get
    return _get()
