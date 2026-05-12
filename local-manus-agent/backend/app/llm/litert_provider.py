"""LiteRT LLM Provider - placeholder for future implementation."""
import json
from typing import AsyncGenerator

from app.llm.base import LocalLLMProvider
from config import LITERT_CONFIG


class LiteRTProvider(LocalLLMProvider):
    """LLM provider for LiteRT-LM (future implementation).

    This provider is a scaffold for integrating LiteRT-LM models.
    To use it:
    1. Set LLM_PROVIDER = "litert" in config.py
    2. Set the model_path in LITERT_CONFIG
    3. Install the LiteRT-LM runtime
    4. Implement the generate/stream methods below
    """

    def __init__(self):
        self.model_path = LITERT_CONFIG["model_path"]
        self.temperature = LITERT_CONFIG["temperature"]
        self.max_tokens = LITERT_CONFIG["max_tokens"]
        self._model = None

    def _load_model(self):
        """Load the LiteRT model from disk.

        TODO: Implement model loading when LiteRT-LM SDK is available.
        Expected usage:
            import litert_lm
            self._model = litert_lm.load(self.model_path)
        """
        raise NotImplementedError(
            "LiteRT-LM provider is not yet implemented. "
            "Please use 'ollama' as LLM_PROVIDER in config.py, "
            "or implement this method when LiteRT-LM SDK is available."
        )

    async def generate(self, prompt: str) -> str:
        """Generate a complete response using LiteRT-LM.

        Args:
            prompt: The input prompt.

        Returns:
            Complete generated text.
        """
        if self._model is None:
            self._load_model()

        # TODO: Replace with actual LiteRT-LM inference call
        # result = self._model.generate(prompt, max_tokens=self.max_tokens)
        # return result.text
        raise NotImplementedError("LiteRT-LM generate not implemented")

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream response tokens using LiteRT-LM.

        Args:
            prompt: The input prompt.

        Yields:
            Individual tokens/chunks.
        """
        if self._model is None:
            self._load_model()

        # TODO: Replace with actual LiteRT-LM streaming
        # for token in self._model.stream(prompt, max_tokens=self.max_tokens):
        #     yield token.text
        raise NotImplementedError("LiteRT-LM stream not implemented")
        yield ""  # Required for generator type

    def tool_call_parse(self, response: str) -> dict | None:
        """Parse a tool call from the LLM response.

        Args:
            response: Raw LLM response text.

        Returns:
            Parsed tool call dict or None.
        """
        try:
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
