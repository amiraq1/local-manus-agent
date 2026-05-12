"""LiteRT-LM Provider - supports local LiteRT models with safe fallback.

Features:
- Tries multiple SDK module names (litert_lm, litertlm, ai_edge_litert, litert)
- Does NOT crash on import if no SDK is available
- Returns comprehensive diagnostics via model_info()
- Clear separation between "model missing" and "SDK missing" states
"""
import json
from pathlib import Path
from typing import AsyncGenerator, Optional

from app.llm.base import LocalLLMProvider
from app.llm.litert_diagnostics import check_sdk_availability
from config import LITERT_CONFIG

# Detect SDK once on import (safely)
_SDK_STATE = check_sdk_availability()
_LITERT_AVAILABLE = _SDK_STATE["sdk_installed"]
_LITERT_MODULE_NAME = _SDK_STATE["sdk_module"]
_LITERT_IMPORT_ERROR = _SDK_STATE["sdk_import_error"]

# Lazy-loaded actual module reference
_sdk_module = None


def _get_sdk():
    """Lazily import the SDK module."""
    global _sdk_module
    if _sdk_module is None and _LITERT_AVAILABLE and _LITERT_MODULE_NAME:
        try:
            _sdk_module = __import__(_LITERT_MODULE_NAME)
        except Exception:
            pass
    return _sdk_module


class LiteRTProvider(LocalLLMProvider):
    """LLM provider for LiteRT-LM local models."""

    def __init__(self):
        self.model_path = LITERT_CONFIG.get("model_path", "")
        self.temperature = LITERT_CONFIG.get("temperature", 0.7)
        self.max_tokens = LITERT_CONFIG.get("max_tokens", 4096)
        self.device = LITERT_CONFIG.get("device", "cpu")
        self.enable_streaming = LITERT_CONFIG.get("enable_streaming", True)
        self._model = None
        self._load_error: str = ""

    def is_available(self) -> bool:
        """True only if SDK is installed AND model file exists."""
        if not _LITERT_AVAILABLE:
            return False
        if not self.model_path:
            return False
        if not Path(self.model_path).exists():
            return False
        return True

    def model_info(self) -> dict:
        """Return comprehensive provider status."""
        model_exists = bool(self.model_path and Path(self.model_path).exists())

        info = {
            "provider": "litert",
            "sdk_installed": _LITERT_AVAILABLE,
            "sdk_module": _LITERT_MODULE_NAME,
            "sdk_import_error": _LITERT_IMPORT_ERROR,
            "model_path": self.model_path,
            "model_exists": model_exists,
            "device": self.device,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "streaming": self.enable_streaming,
            "available": self.is_available(),
        }

        # Status code for precise UI handling
        if not _LITERT_AVAILABLE and model_exists:
            info["status_code"] = "sdk_missing"
            info["error"] = "LiteRT-LM model file is available, but no compatible Python runtime is installed on this system."
        elif not _LITERT_AVAILABLE:
            info["status_code"] = "sdk_missing_no_model"
            info["error"] = f"LiteRT-LM SDK not installed: {_LITERT_IMPORT_ERROR or 'no SDK found'}"
        elif not self.model_path:
            info["status_code"] = "no_model_path"
            info["error"] = "LITERT_CONFIG['model_path'] not set"
        elif not model_exists:
            info["status_code"] = "model_not_found"
            info["error"] = f"Model file not found: {self.model_path}"
        else:
            info["status_code"] = "ready"

        return info

    def _ensure_model(self):
        """Load the model if not already loaded."""
        if self._model is not None:
            return

        if not _LITERT_AVAILABLE:
            raise RuntimeError(
                f"LiteRT-LM SDK is not installed. Tried: {_SDK_STATE['tried_modules']}. "
                f"Last error: {_LITERT_IMPORT_ERROR}\n"
                "Use Ollama as the local LLM, or install LiteRT-LM Python SDK when available."
            )

        if not self.model_path:
            raise RuntimeError("Model path not configured. Set it in Settings → Models.")

        model_file = Path(self.model_path)
        if not model_file.exists():
            raise RuntimeError(f"Model file not found: {self.model_path}")

        sdk = _get_sdk()
        if sdk is None:
            raise RuntimeError("Failed to load LiteRT-LM SDK module")

        # Try common load function names across SDK variants
        try:
            if hasattr(sdk, "load"):
                self._model = sdk.load(self.model_path, device=self.device)
            elif hasattr(sdk, "Model"):
                self._model = sdk.Model(self.model_path)
            elif hasattr(sdk, "load_model"):
                self._model = sdk.load_model(self.model_path)
            else:
                raise RuntimeError(f"SDK '{_LITERT_MODULE_NAME}' has no known load function")
        except Exception as e:
            self._load_error = str(e)
            raise RuntimeError(f"Failed to load LiteRT model: {e}")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a complete response."""
        self._ensure_model()

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        if hasattr(self._model, "generate"):
            result = self._model.generate(prompt, max_tokens=max_tokens, temperature=temperature)
        elif hasattr(self._model, "__call__"):
            result = self._model(prompt, max_tokens=max_tokens)
        else:
            raise RuntimeError("Model does not support generate()")

        return result.text if hasattr(result, "text") else str(result)

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response tokens."""
        self._ensure_model()

        if not self.enable_streaming or not hasattr(self._model, "stream"):
            result = await self.generate(prompt, **kwargs)
            yield result
            return

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        for token in self._model.stream(prompt, max_tokens=max_tokens, temperature=temperature):
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
