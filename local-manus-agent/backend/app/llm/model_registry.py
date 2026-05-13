"""Model Registry - catalog of supported LLM models with download info."""
from pathlib import Path
from config import BASE_DIR

MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODEL_REGISTRY = {
    "ollama-qwen-coder": {
        "id": "ollama-qwen-coder",
        "name": "Ollama qwen2.5-coder:7b",
        "provider": "ollama",
        "description": "Qwen 2.5 Coder 7B via local Ollama instance. Best balance of quality and speed.",
        "expected_filename": "",
        "recommended_path": "",
        "huggingface_repo": "",
        "huggingface_file": "",
        "estimated_size": "4.7 GB",
        "license_note": "",
        "download_commands": [
            "ollama pull qwen2.5-coder:7b",
        ],
    },
    "gemma-e2b-litert": {
        "id": "gemma-e2b-litert",
        "name": "Gemma 3n E2B int4 (LiteRT-LM)",
        "provider": "litert",
        "description": "Google Gemma 3n E2B quantized to int4 for LiteRT-LM. Lightweight, runs on mobile.",
        "expected_filename": "gemma-3n-E2B-it-int4.litertlm",
        "recommended_path": str(MODELS_DIR / "gemma-e2b" / "gemma-3n-E2B-it-int4.litertlm"),
        "huggingface_repo": "google/gemma-3n-E2B-it-litert-lm",
        "huggingface_file": "gemma-3n-E2B-it-int4.litertlm",
        "estimated_size": "2.5 GB",
        "license_note": "Requires accepting Google Gemma license on Hugging Face before download.",
        "download_commands": [
            "pip install -U huggingface_hub",
            "huggingface-cli login",
            "huggingface-cli download google/gemma-3n-E2B-it-litert-lm gemma-3n-E2B-it-int4.litertlm --local-dir models/gemma-e2b",
        ],
    },
    "gemma-e4b-litert": {
        "id": "gemma-e4b-litert",
        "name": "Gemma 3n E4B int4 (LiteRT-LM)",
        "provider": "litert",
        "description": "Google Gemma 3n E4B quantized to int4 for LiteRT-LM. Higher quality, needs more RAM.",
        "expected_filename": "gemma-3n-E4B-it-int4.litertlm",
        "recommended_path": str(MODELS_DIR / "gemma-e4b" / "gemma-3n-E4B-it-int4.litertlm"),
        "huggingface_repo": "google/gemma-3n-E4B-it-litert-lm",
        "huggingface_file": "gemma-3n-E4B-it-int4.litertlm",
        "estimated_size": "4.5 GB",
        "license_note": "Requires accepting Google Gemma license on Hugging Face before download.",
        "download_commands": [
            "pip install -U huggingface_hub",
            "huggingface-cli login",
            "huggingface-cli download google/gemma-3n-E4B-it-litert-lm gemma-3n-E4B-it-int4.litertlm --local-dir models/gemma-e4b",
        ],
    },
    "litert-custom": {
        "id": "litert-custom",
        "name": "Custom LiteRT-LM Model",
        "provider": "litert",
        "description": "Use any .litertlm model file by setting a custom path.",
        "expected_filename": "",
        "recommended_path": "",
        "huggingface_repo": "",
        "huggingface_file": "",
        "estimated_size": "varies",
        "license_note": "",
        "download_commands": [],
    },
}


def get_model_status(model_id: str, user_path: str = "") -> dict:
    """Get status of a model."""
    if model_id not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_id}"}

    model = MODEL_REGISTRY[model_id]
    path = user_path or model["recommended_path"]

    # For ollama, check if ollama is running
    if model["provider"] == "ollama":
        import shutil
        ollama_available = shutil.which("ollama") is not None
        return {
            "id": model_id,
            "name": model["name"],
            "provider": model["provider"],
            "description": model["description"],
            "path": "",
            "exists": ollama_available,
            "file_size": 0,
            "estimated_size": model["estimated_size"],
            "status": "ready" if ollama_available else "missing",
            "license_note": model["license_note"],
            "download_commands": model["download_commands"],
        }

    exists = bool(path) and Path(path).exists()
    size = Path(path).stat().st_size if exists else 0

    # Check if LiteRT SDK is available
    sdk_available = True
    try:
        import litert_lm  # type: ignore
    except ImportError:
        sdk_available = False

    status = "ready" if exists and sdk_available else "missing"
    if exists and not sdk_available:
        status = "sdk_missing"

    return {
        "id": model_id,
        "name": model["name"],
        "provider": model["provider"],
        "description": model["description"],
        "path": path,
        "exists": exists,
        "sdk_available": sdk_available,
        "file_size": size,
        "estimated_size": model["estimated_size"],
        "status": status,
        "license_note": model["license_note"],
        "download_commands": model["download_commands"],
    }


def get_all_models_status(user_paths: dict = None) -> list[dict]:
    """Get status of all registered and imported models."""
    from app.user_config_manager import load_user_config
    
    paths = user_paths or {}
    results = []
    
    # Static registry
    for model_id in MODEL_REGISTRY:
        user_path = paths.get(model_id, "")
        results.append(get_model_status(model_id, user_path))
        
    # Imported models
    cfg = load_user_config()
    imported = cfg.get("imported_models", [])
    
    for imp in imported:
        path = imp.get("path", "")
        exists = bool(path) and Path(path).exists()
        size = Path(path).stat().st_size if exists else 0
        
        sdk_available = True
        try:
            import litert_lm  # type: ignore
        except ImportError:
            sdk_available = False
            
        status = "ready" if exists and sdk_available else "missing"
        if exists and not sdk_available:
            status = "sdk_missing"
            
        results.append({
            "id": imp["id"],
            "name": imp["name"],
            "provider": imp["provider"],
            "description": "Imported local model.",
            "path": path,
            "exists": exists,
            "sdk_available": sdk_available,
            "file_size": size,
            "estimated_size": f"{imp.get('size', 0) / (1024**3):.1f} GB",
            "status": status,
            "license_note": "Imported locally",
            "download_commands": [],
            "is_imported": True
        })
        
    return results
