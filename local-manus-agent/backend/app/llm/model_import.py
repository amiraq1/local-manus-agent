"""Model Import - chunked upload and registration of .litertlm files."""
import hashlib
import os
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from config import BASE_DIR

MODELS_DIR = BASE_DIR / "models"
IMPORTED_DIR = MODELS_DIR / "imported"
UPLOADS_DIR = MODELS_DIR / ".uploads"
IMPORTED_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = [".litertlm"]
BLOCKED_EXTENSIONS = [".exe", ".bat", ".ps1", ".cmd", ".dll", ".sh", ".msi", ".com"]
MAX_FILE_SIZE = 8 * 1024 * 1024 * 1024  # 8GB
CHUNK_SIZE = 50 * 1024 * 1024  # 50MB

# Active imports
_active_imports: dict[str, dict] = {}


def start_import(filename: str, size: int, model_name: str = "") -> dict:
    """Start a model import session.

    Args:
        filename: Original filename.
        size: Total file size in bytes.
        model_name: Optional display name.

    Returns:
        Dict with import_id, chunk_size, accepted status.
    """
    # Validate extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"accepted": False, "error": f"Only .litertlm files allowed. Got: {ext}"}

    if ext in BLOCKED_EXTENSIONS:
        _log_security("import_blocked", filename, f"Blocked extension: {ext}")
        return {"accepted": False, "error": f"Blocked file type: {ext}"}

    # Validate filename (no path traversal)
    safe_name = _sanitize_filename(filename)
    if not safe_name:
        return {"accepted": False, "error": "Invalid filename"}

    # Validate size
    if size <= 0:
        return {"accepted": False, "error": "Invalid file size"}
    if size > MAX_FILE_SIZE:
        return {"accepted": False, "error": f"File too large. Max: {MAX_FILE_SIZE // (1024**3)}GB"}

    # Create import session
    import_id = str(uuid.uuid4())[:12]
    upload_dir = UPLOADS_DIR / import_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    total_chunks = (size + CHUNK_SIZE - 1) // CHUNK_SIZE

    _active_imports[import_id] = {
        "id": import_id,
        "filename": safe_name,
        "model_name": model_name or Path(safe_name).stem,
        "size": size,
        "total_chunks": total_chunks,
        "received_chunks": 0,
        "upload_dir": str(upload_dir),
        "started_at": time.time(),
        "status": "uploading",
    }

    return {
        "accepted": True,
        "import_id": import_id,
        "chunk_size": CHUNK_SIZE,
        "total_chunks": total_chunks,
        "filename": safe_name,
    }


def receive_chunk(import_id: str, chunk_index: int, data: bytes) -> dict:
    """Receive a chunk of the model file.

    Args:
        import_id: Import session ID.
        chunk_index: Zero-based chunk index.
        data: Chunk binary data.

    Returns:
        Dict with success status.
    """
    if import_id not in _active_imports:
        return {"success": False, "error": "Import session not found"}

    session = _active_imports[import_id]
    upload_dir = Path(session["upload_dir"])

    if not upload_dir.exists():
        return {"success": False, "error": "Upload directory missing"}

    # Write chunk
    chunk_path = upload_dir / f"{chunk_index:06d}.part"
    chunk_path.write_bytes(data)

    session["received_chunks"] += 1

    return {
        "success": True,
        "chunk_index": chunk_index,
        "received": session["received_chunks"],
        "total": session["total_chunks"],
    }


def finish_import(import_id: str) -> dict:
    """Finish import - combine chunks and register model.

    Args:
        import_id: Import session ID.

    Returns:
        Dict with model_id, path, sha256.
    """
    if import_id not in _active_imports:
        return {"success": False, "error": "Import session not found"}

    session = _active_imports[import_id]
    upload_dir = Path(session["upload_dir"])
    filename = session["filename"]

    # Combine chunks
    dest_path = IMPORTED_DIR / filename
    sha256 = hashlib.sha256()

    try:
        with open(dest_path, "wb") as out:
            for i in range(session["total_chunks"]):
                chunk_path = upload_dir / f"{i:06d}.part"
                if not chunk_path.exists():
                    return {"success": False, "error": f"Missing chunk {i}"}
                chunk_data = chunk_path.read_bytes()
                out.write(chunk_data)
                sha256.update(chunk_data)
    except Exception as e:
        return {"success": False, "error": f"Failed to combine chunks: {e}"}

    file_hash = sha256.hexdigest()
    file_size = dest_path.stat().st_size

    # Verify size
    if abs(file_size - session["size"]) > CHUNK_SIZE:
        dest_path.unlink(missing_ok=True)
        return {"success": False, "error": "Size mismatch after combining"}

    # Register in user_config
    model_id = f"imported-{import_id}"
    _register_imported_model(model_id, session["model_name"], str(dest_path), file_size, file_hash)

    # Cleanup upload dir
    shutil.rmtree(str(upload_dir), ignore_errors=True)
    session["status"] = "completed"

    return {
        "success": True,
        "model_id": model_id,
        "name": session["model_name"],
        "path": str(dest_path),
        "size": file_size,
        "sha256": file_hash,
    }


def get_import_status(import_id: str) -> dict:
    """Get import progress."""
    if import_id not in _active_imports:
        return {"error": "Import session not found"}

    session = _active_imports[import_id]
    progress = 0
    if session["total_chunks"] > 0:
        progress = int((session["received_chunks"] / session["total_chunks"]) * 100)

    return {
        "import_id": import_id,
        "status": session["status"],
        "filename": session["filename"],
        "progress": progress,
        "received_chunks": session["received_chunks"],
        "total_chunks": session["total_chunks"],
        "size": session["size"],
    }


def cancel_import(import_id: str) -> dict:
    """Cancel an import and clean up."""
    if import_id not in _active_imports:
        return {"success": True, "message": "Not found"}

    session = _active_imports[import_id]
    upload_dir = Path(session["upload_dir"])
    shutil.rmtree(str(upload_dir), ignore_errors=True)
    del _active_imports[import_id]

    return {"success": True, "message": "Import cancelled"}


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename - remove path components and dangerous chars."""
    # Take only the basename
    name = Path(filename).name
    # Remove path traversal
    if ".." in name or "/" in name or "\\" in name:
        return ""
    # Keep only safe chars
    name = re.sub(r"[^\w\-.]", "_", name)
    if not name or name.startswith("."):
        return ""
    return name


def _register_imported_model(model_id: str, name: str, path: str, size: int, sha256: str):
    """Register an imported model in user_config."""
    from app.user_config_manager import load_user_config, save_user_config

    cfg = load_user_config()
    if "imported_models" not in cfg:
        cfg["imported_models"] = []

    cfg["imported_models"].append({
        "id": model_id,
        "name": name,
        "provider": "litert",
        "path": path,
        "size": size,
        "sha256": sha256,
        "created_at": time.time(),
        "source": "local_import",
    })

    # Also set in model_paths
    if "model_paths" not in cfg:
        cfg["model_paths"] = {}
    cfg["model_paths"][model_id] = path

    save_user_config(cfg)


def _log_security(event_type: str, target: str, reason: str):
    """Log a security event."""
    try:
        from app.security.audit_log import log_security_event
        log_security_event(None, event_type, "high", "model_import", target, "deny", reason)
    except Exception:
        pass
