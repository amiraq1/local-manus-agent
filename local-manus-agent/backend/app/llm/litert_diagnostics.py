"""LiteRT-LM Diagnostics - detect SDK/CLI availability and model runtime status."""
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
    """Check which LiteRT-LM SDK (if any) is available."""
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
    """Get comprehensive LiteRT-LM diagnostics (SDK + CLI)."""
    sdk = check_sdk_availability()

    # Check CLI availability
    from app.llm.litert_cli_provider import find_cli, get_cli_version
    try:
        from app.user_config_manager import load_user_config
        cfg = load_user_config()
        explicit_cli = cfg.get("llm", {}).get("litert_cli_path", "")
    except Exception:
        explicit_cli = ""

    cli_path = find_cli(explicit_cli)
    cli_available = bool(cli_path)
    cli_version = get_cli_version(cli_path) if cli_path else ""

    model_exists = False
    model_size = 0
    if model_path:
        p = Path(model_path)
        model_exists = p.exists() and p.is_file()
        if model_exists:
            model_size = p.stat().st_size

    runtime_available = (cli_available or sdk["sdk_installed"]) and model_exists

    # Status determination
    if cli_available and model_exists:
        status = "ready_cli"
        message = f"LiteRT-LM CLI ready. Model available."
        suggestions = []
    elif sdk["sdk_installed"] and model_exists:
        status = "ready_sdk"
        message = "LiteRT-LM Python SDK and model are both available."
        suggestions = []
    elif model_exists and not cli_available and not sdk["sdk_installed"]:
        status = "model_ready_runtime_missing"
        message = "Model file is available, but no LiteRT-LM runtime (CLI or Python SDK) is installed."
        suggestions = [
            "Install litert-lm CLI (recommended on Windows)",
            "Use the Android Nabd app for .litertlm runtime",
            "Use Ollama on Windows/Linux/macOS as the local LLM",
            "Install ai-edge-litert Python SDK when officially released",
        ]
    elif not model_exists and (cli_available or sdk["sdk_installed"]):
        status = "runtime_ready_model_missing"
        message = "LiteRT runtime installed, but no model file is configured."
        suggestions = ["Download a .litertlm model and set its path in Settings → Models"]
    else:
        status = "not_configured"
        message = "Neither runtime nor model is available."
        suggestions = [
            "Download a .litertlm model (e.g. Gemma E2B from Hugging Face)",
            "Install litert-lm CLI or Python SDK",
        ]

    return {
        "sdk_installed": sdk["sdk_installed"],
        "sdk_module": sdk["sdk_module"],
        "sdk_version": sdk["sdk_version"],
        "sdk_import_error": sdk["sdk_import_error"],
        "tried_modules": sdk["tried_modules"],
        "cli_available": cli_available,
        "cli_path": cli_path or "",
        "cli_version": cli_version,
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
