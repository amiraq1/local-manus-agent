"""LiteRT-LM Provider - supports local LiteRT models with safe fallback.

If the LiteRT-LM SDK is not installed, this provider:
- Does NOT crash on import
- Returns is_available() = False
- Gives a clear error message

To use:
1. Install LiteRT-LM SDK: pip install litert-lm (when available)
2. Set LLM_PROVIDER = "litert" in config.py
3. Set LITERT_MODEL_PATH to your model file
"""
import json
from pathlib import Path
from typing import AsyncGenerator

from app.llm.base import LocalLLMProvider
from config import LITERT_CONFIG

# Try to import LiteRT-LM SDK (graceful failure)
_LITERT_AVAILABLE = False
_LITERT_IMPORT_ERROR = ""

try:
    import litert_lm  # type: ignore
    _LITERT_AVAILABLE = True
except ImportError as e:
    _LITERT_IMPORT_ERROR = str(e)
except Exception as e:
    _LITERT_IMPORT_ERROR = f"Unexpected error importing litert_lm: {e}"


class LiteRTProvider(LocalLLMProvider):
    """LLM provider for LiteRT-LM local models.

    Handles graceful degradation when SDK is not installed.
    """

    def __init__(self):
        self.model_path = LITERT_CONFIG.get("model_path", "")
        self.temperature = LITERT_CONFIG.get("temperature", 0.7)
        self.max_tokens = LITERT_CONFIG.get("max_tokens", 4096)
        self.device = LITERT_CONFIG.get("device", "cpu")
        self.enable_streaming = LITERT_CONFIG.get("enable_streaming", True)
        self._model = None
        self._load_error: str = ""

    def is_available(self) -> bool:
        """Check if LiteRT-LM is ready to use."""
        if not _LITERT_AVAILABLE:
            return False
        if not self.model_path:
            return False
        if not Path(self.model_path).exists():
            return False
        return True

    def model_info(self) -> dict:
        """Return provider status info."""
        info = {
            "provider": "litert",
            "sdk_installed": _LITERT_AVAILABLE,
            "model_path": self.model_path,
            "model_exists": bool(self.model_path and Path(self.model_path).exists()),
            "device": self.device,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "streaming": self.enable_streaming,
            "available": self.is_available(),
        }
        if not _LITERT_AVAILABLE:
            info["error"] = f"LiteRT-LM SDK not installed: {_LITERT_IMPORT_ERROR}"
        elif not self.model_path:
            info["error"] = "LITERT_MODEL_PATH not configured in config.py"
        elif not Path(self.model_path).exists():
            info["error"] = f"Model file not found: {self.model_path}"
        return info

    def _ensure_model(self):
        """Load the model if not already loaded."""
        if self._model is not None:
            return

        if not _LITERT_AVAILABLE:
            raise RuntimeError(
                "LiteRT-LM SDK is not installed. "
                "Install it with: pip install litert-lm\n"
                "Or set LLM_PROVIDER='ollama' in config.py to use Ollama instead."
            )

        if not self.model_path:
            raise RuntimeError(
                "LITERT_MODEL_PATH is not configured. "
                "Set it in config.py LITERT_CONFIG['model_path']."
            )

        model_file = Path(self.model_path)
        if not model_file.exists():
            raise RuntimeError(
                f"Model file not found: {self.model_path}\n"
                "Download a compatible model and update LITERT_CONFIG['model_path']."
            )

        # Load the model using LiteRT-LM SDK
        try:
            self._model = litert_lm.load(  # type: ignore
                self.model_path,
                device=self.device,
            )
        except Exception as e:
            self._load_error = str(e)
            raise RuntimeError(f"Failed to load LiteRT model: {e}")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a complete response using LiteRT-LM."""
        self._ensure_model()

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        # LiteRT-LM SDK call (when available)
        result = self._model.generate(  # type: ignore
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return result.text if hasattr(result, "text") else str(result)

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response tokens using LiteRT-LM."""
        self._ensure_model()

        if not self.enable_streaming:
            # Fallback to full generation
            result = await self.generate(prompt, **kwargs)
            yield result
            return

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        # LiteRT-LM SDK streaming call (when available)
        for token in self._model.stream(  # type: ignore
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            text = token.text if hasattr(token, "text") else str(token)
            if text:
                yield text

    def tool_call_parse(self, response: str) -> dict | None:
        """Parse a tool call from the LLM response."""
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
