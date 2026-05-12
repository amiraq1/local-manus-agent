"""File operation tools for the agent - uses per-task workspace."""
import uuid
from pathlib import Path

from app.workspace.manager import (
    get_current_task_id,
    get_current_files_dir,
    resolve_safe_path,
)
from app import database as db


def read_file(path: str) -> dict:
    """Read a file from the current task's workspace.

    Args:
        path: Relative path within task files directory.

    Returns:
        Dict with success status and file content or error.
    """
    task_id = get_current_task_id()
    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    try:
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}
        if not file_path.is_file():
            return {"success": False, "error": f"Not a file: {path}"}

        content = file_path.read_text(encoding="utf-8")
        return {"success": True, "content": content, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(path: str, content: str) -> dict:
    """Write content to a file in the current task's workspace.

    Records the change as a diff and registers as an artifact.

    Args:
        path: Relative path within task files directory.
        content: File content to write.

    Returns:
        Dict with success status and change info.
    """
    from app.tools.diff_tools import preview_file_change

    task_id = get_current_task_id()
    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    # Use diff system to track changes
    result = preview_file_change(path, content)
    if not result.get("success"):
        return result

    # Write to disk
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Register as artifact
    artifact_id = str(uuid.uuid4())[:12]
    ext = file_path.suffix.lower()
    mime = _guess_mime(ext)
    db.create_artifact(
        artifact_id=artifact_id,
        task_id=task_id,
        artifact_type="file",
        name=Path(path).name,
        path=path,
        mime_type=mime,
        size=len(content),
    )

    return {
        "success": True,
        "path": path,
        "size": len(content),
        "change_id": result.get("change_id"),
        "artifact_id": artifact_id,
        "diff": result.get("diff", ""),
        "status": result.get("status"),
    }


def edit_file(path: str, instructions: str) -> dict:
    """Edit an existing file. Uses write_file with diff tracking.

    Args:
        path: Relative path within task files directory.
        instructions: New content for the file.

    Returns:
        Dict with success status and diff info.
    """
    task_id = get_current_task_id()
    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    if not file_path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    return write_file(path, instructions)


def list_files(path: str = "") -> list[dict]:
    """List files in the current task's workspace.

    Args:
        path: Optional subdirectory path.

    Returns:
        List of file/directory info dicts.
    """
    task_id = get_current_task_id()
    files_dir = get_current_files_dir()

    try:
        if path:
            safe, target, reason = resolve_safe_path(task_id, path, "files")
            if not safe:
                return [{"error": reason}]
        else:
            target = files_dir

        if not target.exists():
            return []

        items = []
        for item in sorted(target.rglob("*")):
            rel_path = item.relative_to(files_dir)
            items.append({
                "path": str(rel_path).replace("\\", "/"),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
            })
        return items
    except Exception as e:
        return [{"error": str(e)}]


def create_folder(path: str) -> dict:
    """Create a directory in the current task's workspace.

    Args:
        path: Relative path for the new directory.

    Returns:
        Dict with success status.
    """
    task_id = get_current_task_id()
    safe, folder_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _guess_mime(ext: str) -> str:
    """Guess MIME type from file extension."""
    mimes = {
        ".html": "text/html", ".htm": "text/html",
        ".css": "text/css",
        ".js": "application/javascript", ".jsx": "application/javascript",
        ".ts": "text/typescript", ".tsx": "text/typescript",
        ".json": "application/json",
        ".py": "text/x-python",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml", ".webp": "image/webp",
    }
    return mimes.get(ext, "application/octet-stream")
