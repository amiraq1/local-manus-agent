"""User Config Manager - persists user preferences without modifying config.py."""
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "user_config.json"

_DEFAULT = {
    "active_preset": "ollama-qwen-coder",
    "model_paths": {},
    "ollama_base_url": "http://localhost:11434",
    "litert_device": "cpu",
    "litert_temperature": 0.7,
    "litert_max_tokens": 4096,
    "allow_fallback": True,
}


def load_user_config() -> dict:
    """Load user config from JSON file."""
    if not CONFIG_FILE.exists():
        save_user_config(_DEFAULT)
        return _DEFAULT.copy()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        for k, v in _DEFAULT.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return _DEFAULT.copy()


def save_user_config(data: dict):
    """Save user config to JSON file."""
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


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
    return load_user_config().get("active_preset", "ollama-qwen-coder")


def set_active_preset(preset_id: str):
    """Set the active preset."""
    cfg = load_user_config()
    cfg["active_preset"] = preset_id
    save_user_config(cfg)
