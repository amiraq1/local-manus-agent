"""LLM Provider Factory - handles provider selection and fallback logic."""
import logging
from typing import Optional

from app.llm.base import LocalLLMProvider

logger = logging.getLogger(__name__)

_provider_instance: Optional[LocalLLMProvider] = None
_fallback_used: bool = False
_provider_error: str = ""


def get_llm_provider() -> LocalLLMProvider:
    """Get the configured LLM provider with fallback support.

    Logic:
    - If LLM_PROVIDER=ollama → use Ollama
    - If LLM_PROVIDER=litert and available → use LiteRT
    - If LLM_PROVIDER=litert and NOT available:
      - If LITERT_ALLOW_FALLBACK=True → use Ollama with warning
      - If LITERT_ALLOW_FALLBACK=False → raise error

    Returns:
        Active LocalLLMProvider instance.
    """
    global _provider_instance, _fallback_used, _provider_error

    if _provider_instance is not None:
        return _provider_instance

    from config import LLM_PROVIDER

    if LLM_PROVIDER == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        _provider_instance = OllamaProvider()
        _fallback_used = False
        _provider_error = ""

    elif LLM_PROVIDER == "litert":
        # Try CLI provider first (works without Python SDK)
        from app.llm.litert_cli_provider import LiteRTCLIProvider
        cli = LiteRTCLIProvider()

        if cli.is_available():
            _provider_instance = cli
            _fallback_used = False
            _provider_error = ""
            return _provider_instance

        # Fall back to Python SDK provider
        from app.llm.litert_provider import LiteRTProvider
        litert = LiteRTProvider()

        if litert.is_available():
            _provider_instance = litert
            _fallback_used = False
            _provider_error = ""
        else:
            # Neither CLI nor SDK - check external fallback
            from config import LITERT_CONFIG
            allow_fallback = LITERT_CONFIG.get("allow_fallback", True)
            fallback_provider = LITERT_CONFIG.get("fallback_provider", "ollama")

            cli_info = cli.model_info()
            sdk_info = litert.model_info()
            _provider_error = cli_info.get("error") or sdk_info.get("error", "LiteRT-LM not available")

            if allow_fallback and fallback_provider == "ollama":
                logger.warning(f"LiteRT-LM not available ({_provider_error}). Falling back to Ollama.")
                from app.llm.ollama_provider import OllamaProvider
                _provider_instance = OllamaProvider()
                _fallback_used = True
            else:
                raise RuntimeError(
                    f"LiteRT-LM is not available: {_provider_error}\n"
                    f"Install litert-lm CLI or Python SDK, or set LLM_PROVIDER='ollama'."
                )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'ollama' or 'litert'.")

    return _provider_instance


def get_provider_status() -> dict:
    """Get detailed status of the LLM provider system.

    Returns:
        Dict with provider status, fallback info, and availability.
    """
    from config import LLM_PROVIDER, LITERT_CONFIG

    status = {
        "configured_provider": LLM_PROVIDER,
        "active_provider": None,
        "model": None,
        "available": False,
        "fallback_used": _fallback_used,
        "fallback_provider": LITERT_CONFIG.get("fallback_provider", "ollama"),
        "fallback_allowed": LITERT_CONFIG.get("allow_fallback", True),
        "error": _provider_error or None,
    }

    try:
        provider = get_llm_provider()
        info = provider.model_info()
        status["active_provider"] = info.get("provider", LLM_PROVIDER)
        status["model"] = info.get("model", info.get("model_path", ""))
        status["available"] = provider.is_available()
        status["provider_info"] = info
    except Exception as e:
        status["error"] = str(e)
        status["available"] = False

    return status


def reset_provider():
    """Reset the provider instance (for testing or config changes)."""
    global _provider_instance, _fallback_used, _provider_error
    _provider_instance = None
    _fallback_used = False
    _provider_error = ""
