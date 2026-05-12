"""Model Registry - catalog of supported LLM models with download info."""
from pathlib import Path
from config import BASE_DIR

MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODEL_REGISTRY = {
    "gemma-e2b-litert": {
        "name": "Gemma 3n E2B int4 (LiteRT-LM)",
        "provider": "litert",
        "expected_filename": "gemma-3n-E2B-it-int4.litertlm",
        "recommended_path": str(MODELS_DIR / "gemma-e2b" / "gemma-3n-E2B-it-int4.litertlm"),
        "huggingface_repo": "google/gemma-3n-E2B-it-litert-lm",
        "huggingface_file": "gemma-3n-E2B-it-int4.litertlm",
        "estimated_size": "2.5 GB",
        "license_note": "Requires accepting Google Gemma license on Hugging Face before download.",
        "install_commands": [
            "pip install -U huggingface_hub",
            "huggingface-cli login",
            "huggingface-cli download google/gemma-3n-E2B-it-litert-lm gemma-3n-E2B-it-int4.litertlm --local-dir models/gemma-e2b",
        ],
    },
    "gemma-e4b-litert": {
        "name": "Gemma 3n E4B int4 (LiteRT-LM)",
        "provider": "litert",
        "expected_filename": "gemma-3n-E4B-it-int4.litertlm",
        "recommended_path": str(MODELS_DIR / "gemma-e4b" / "gemma-3n-E4B-it-int4.litertlm"),
        "huggingface_repo": "google/gemma-3n-E4B-it-litert-lm",
        "huggingface_file": "gemma-3n-E4B-it-int4.litertlm",
        "estimated_size": "4.5 GB",
        "license_note": "Requires accepting Google Gemma license on Hugging Face before download.",
        "install_commands": [
            "pip install -U huggingface_hub",
            "huggingface-cli login",
            "huggingface-cli download google/gemma-3n-E4B-it-litert-lm gemma-3n-E4B-it-int4.litertlm --local-dir models/gemma-e4b",
        ],
    },
    "litert-custom": {
        "name": "Custom LiteRT-LM Model",
        "provider": "litert",
        "expected_filename": "",
        "recommended_path": "",
        "huggingface_repo": "",
        "huggingface_file": "",
        "estimated_size": "varies",
        "license_note": "",
        "install_commands": [],
    },
}


def get_model_status(model_id: str, user_path: str = "") -> dict:
    """Get status of a model."""
    if model_id not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_id}"}

    model = MODEL_REGISTRY[model_id]
    path = user_path or model["recommended_path"]

    exists = bool(path) and Path(path).exists()
    size = Path(path).stat().st_size if exists else 0

    return {
        "id": model_id,
        "name": model["name"],
        "provider": model["provider"],
        "path": path,
        "exists": exists,
        "file_size": size,
        "estimated_size": model["estimated_size"],
        "status": "ready" if exists else "missing",
        "license_note": model["license_note"],
    }


def get_all_models_status(user_paths: dict = None) -> list[dict]:
    """Get status of all registered models."""
    paths = user_paths or {}
    results = []
    for model_id in MODEL_REGISTRY:
        user_path = paths.get(model_id, "")
        results.append(get_model_status(model_id, user_path))
    return results
