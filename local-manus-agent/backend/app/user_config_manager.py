"""User Config Manager - persists structured settings."""
import json
from pathlib import Path

from app.config.settings_schema import DEFAULT_SETTINGS, validate_settings

CONFIG_FILE = Path(__file__).parent / "user_config.json"


def load_user_config() -> dict:
    """Load user config, merging with defaults for missing keys."""
    if not CONFIG_FILE.exists():
        save_user_config(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        # Deep merge with defaults
        merged = _deep_merge(DEFAULT_SETTINGS.copy(), data)
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_user_config(data: dict):
    """Save user config to JSON file."""
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def update_settings(partial: dict) -> tuple[bool, dict, list[str]]:
    """Update settings with validation.

    Args:
        partial: Partial settings dict to merge.

    Returns:
        Tuple of (success, full_settings, errors).
    """
    current = load_user_config()
    merged = _deep_merge(current, partial)
    valid, validated, errors = validate_settings(merged)
    if valid:
        save_user_config(validated)
        return True, validated, []
    return False, current, errors


def reset_settings() -> dict:
    """Reset to default settings."""
    save_user_config(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()


def get_model_path(model_id: str) -> str:
    """Get the user-configured path for a model."""
    cfg = load_user_config()
    return cfg.get("model_paths", {}).get(model_id, "")


def set_model_path(model_id: str, path: str):
    """Set the path for a model."""
    cfg = load_user_config()
    if "model_paths" not in cfg:
        cfg["model_paths"] = {}
    cfg["model_paths"][model_id] = path
    save_user_config(cfg)


def get_active_preset() -> str:
    """Get the active preset."""
    cfg = load_user_config()
    return cfg.get("llm", {}).get("active_preset", "ollama-qwen-coder")


def set_active_preset(preset_id: str):
    """Set the active preset."""
    cfg = load_user_config()
    if "llm" not in cfg:
        cfg["llm"] = {}
    cfg["llm"]["active_preset"] = preset_id
    save_user_config(cfg)


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
