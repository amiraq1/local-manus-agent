"""LiteRT-LM Diagnostics - detect SDK availability and model runtime status."""
import platform
import sys
from pathlib import Path
from typing import Optional

# Try multiple possible SDK module names
_SDK_CANDIDATES = [
    "litert_lm",
    "litertlm",
    "ai_edge_litert",
    "litert",
]


def check_sdk_availability() -> dict:
    """Check which LiteRT-LM SDK (if any) is available.

    Returns:
        Dict with sdk_installed, sdk_module, sdk_version, sdk_import_error.
    """
    result = {
        "sdk_installed": False,
        "sdk_module": None,
        "sdk_version": None,
        "sdk_import_error": "",
        "tried_modules": [],
    }

    errors = []
    for module_name in _SDK_CANDIDATES:
        result["tried_modules"].append(module_name)
        try:
            mod = __import__(module_name)
            result["sdk_installed"] = True
            result["sdk_module"] = module_name
            result["sdk_version"] = getattr(mod, "__version__", "unknown")
            return result
        except ImportError as e:
            errors.append(f"{module_name}: {e}")
        except Exception as e:
            errors.append(f"{module_name}: {type(e).__name__}: {e}")

    result["sdk_import_error"] = "; ".join(errors)
    return result


def get_full_diagnostics(model_path: str = "", device: str = "cpu") -> dict:
    """Get comprehensive LiteRT-LM diagnostics.

    Args:
        model_path: Path to the .litertlm model file.
        device: Target device (cpu/gpu).

    Returns:
        Full diagnostic report.
    """
    sdk = check_sdk_availability()

    model_exists = False
    model_size = 0
    if model_path:
        p = Path(model_path)
        model_exists = p.exists() and p.is_file()
        if model_exists:
            model_size = p.stat().st_size

    runtime_available = sdk["sdk_installed"] and model_exists

    # Build status message
    if not sdk["sdk_installed"] and model_exists:
        status = "model_ready_sdk_missing"
        message = "LiteRT-LM model file is available, but no compatible Python runtime is installed on this system."
        suggestions = [
            "Use the Android Nabd app for .litertlm runtime",
            "Use Ollama on Windows/Linux/macOS as the local LLM",
            "Wait for LiteRT-LM Python SDK public release",
            "Install ai-edge-litert when officially released",
        ]
    elif sdk["sdk_installed"] and not model_exists:
        status = "sdk_ready_model_missing"
        message = "LiteRT-LM SDK is installed, but no model file is configured."
        suggestions = ["Set model path in Settings → Models"]
    elif sdk["sdk_installed"] and model_exists:
        status = "ready"
        message = "LiteRT-LM runtime and model are both available."
        suggestions = []
    else:
        status = "not_configured"
        message = "Neither SDK nor model is available."
        suggestions = [
            "Download a .litertlm model (e.g. Gemma E2B from Hugging Face)",
            "Install LiteRT-LM SDK when available",
        ]

    return {
        "sdk_installed": sdk["sdk_installed"],
        "sdk_module": sdk["sdk_module"],
        "sdk_version": sdk["sdk_version"],
        "sdk_import_error": sdk["sdk_import_error"],
        "tried_modules": sdk["tried_modules"],
        "model_path": model_path,
        "model_path_exists": model_exists,
        "model_size": model_size,
        "device": device,
        "runtime_available": runtime_available,
        "status": status,
        "message": message,
        "suggestions": suggestions,
        "platform": {
            "os": sys.platform,
            "python": sys.version.split()[0],
            "machine": platform.machine(),
        },
    }
