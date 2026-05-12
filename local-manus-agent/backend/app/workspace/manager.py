"""Workspace Manager - creates and manages per-task isolated workspaces.

Each task gets its own directory structure:
  tasks/{task_id}/
    files/          - project files created by the agent
    screenshots/    - browser screenshots
    logs/           - execution logs
    artifacts/      - generated artifacts (reports, archives)
    preview/        - preview-related files
"""
import os
import shutil
from pathlib import Path
from typing import Optional

from config import BASE_DIR

# Root directory for all task workspaces
TASKS_ROOT = BASE_DIR / "workspace" / "tasks"
TASKS_ROOT.mkdir(parents=True, exist_ok=True)

# Legacy workspace for backward compatibility
LEGACY_WORKSPACE = BASE_DIR / "workspace"

# Subdirectories for each task
TASK_SUBDIRS = ["files", "screenshots", "logs", "artifacts", "preview"]


def create_task_workspace(task_id: str) -> Path:
    """Create a new workspace for a task with all subdirectories.

    Args:
        task_id: Unique task identifier.

    Returns:
        Path to the task workspace root.
    """
    task_dir = TASKS_ROOT / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    for subdir in TASK_SUBDIRS:
        (task_dir / subdir).mkdir(exist_ok=True)
    return task_dir


def get_task_workspace(task_id: str) -> Path:
    """Get the workspace root for a task, creating if needed.

    Args:
        task_id: Unique task identifier.

    Returns:
        Path to the task workspace root.
    """
    task_dir = TASKS_ROOT / task_id
    if not task_dir.exists():
        return create_task_workspace(task_id)
    return task_dir


def get_files_dir(task_id: str) -> Path:
    """Get the files directory for a task."""
    return get_task_workspace(task_id) / "files"


def get_screenshots_dir(task_id: str) -> Path:
    """Get the screenshots directory for a task."""
    return get_task_workspace(task_id) / "screenshots"


def get_logs_dir(task_id: str) -> Path:
    """Get the logs directory for a task."""
    return get_task_workspace(task_id) / "logs"


def get_artifacts_dir(task_id: str) -> Path:
    """Get the artifacts directory for a task."""
    return get_task_workspace(task_id) / "artifacts"


def get_preview_dir(task_id: str) -> Path:
    """Get the preview directory for a task."""
    return get_task_workspace(task_id) / "preview"


def resolve_safe_path(task_id: str, relative_path: str, subdir: str = "files") -> tuple[bool, Path, str]:
    """Resolve a relative path safely within a task workspace.

    Prevents path traversal, absolute paths, and symlinks outside workspace.

    Args:
        task_id: Task identifier.
        relative_path: Relative path to resolve.
        subdir: Subdirectory within task workspace (default: "files").

    Returns:
        Tuple of (is_safe, resolved_path, error_message).
    """
    # Block absolute paths
    if os.path.isabs(relative_path):
        return False, Path(), "Absolute paths are not allowed"

    # Block path traversal
    if ".." in relative_path.replace("\\", "/").split("/"):
        return False, Path(), "Path traversal (..) is not allowed"

    # Get base directory
    task_dir = get_task_workspace(task_id)
    base_dir = task_dir / subdir

    # Resolve the full path
    resolved = (base_dir / relative_path).resolve()

    # Ensure it's within the task workspace
    base_resolved = base_dir.resolve()
    if not str(resolved).startswith(str(base_resolved)):
        return False, Path(), f"Path escapes task workspace: {relative_path}"

    # Check for symlinks pointing outside
    if resolved.exists() and resolved.is_symlink():
        link_target = resolved.resolve()
        if not str(link_target).startswith(str(base_resolved)):
            return False, Path(), "Symlink points outside workspace"

    return True, resolved, "OK"


def cleanup_task_workspace(task_id: str) -> dict:
    """Remove a task's workspace entirely.

    Args:
        task_id: Task identifier.

    Returns:
        Dict with success status.
    """
    task_dir = TASKS_ROOT / task_id
    if not task_dir.exists():
        return {"success": True, "message": "Workspace does not exist"}

    try:
        shutil.rmtree(str(task_dir))
        return {"success": True, "task_id": task_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_task_workspaces() -> list[dict]:
    """List all existing task workspaces."""
    workspaces = []
    if not TASKS_ROOT.exists():
        return workspaces
    for item in sorted(TASKS_ROOT.iterdir()):
        if item.is_dir():
            files_count = sum(1 for _ in (item / "files").rglob("*") if _.is_file()) if (item / "files").exists() else 0
            workspaces.append({
                "task_id": item.name,
                "path": str(item.relative_to(BASE_DIR)),
                "files_count": files_count,
            })
    return workspaces


# Module-level current task_id
_current_task_id: Optional[str] = None


def set_current_task_id(task_id: str):
    """Set the current task ID for workspace operations."""
    global _current_task_id
    _current_task_id = task_id
    # Ensure workspace exists
    create_task_workspace(task_id)


def get_current_task_id() -> str:
    """Get the current task ID."""
    return _current_task_id or "default"


def get_current_files_dir() -> Path:
    """Get the files directory for the current task."""
    return get_files_dir(get_current_task_id())


def get_current_screenshots_dir() -> Path:
    """Get the screenshots directory for the current task."""
    return get_screenshots_dir(get_current_task_id())
