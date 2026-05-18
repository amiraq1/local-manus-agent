"""Diff Engine - generates and manages file diffs before applying changes."""
import difflib
import uuid
from pathlib import Path
from typing import Optional

from app.workspace.manager import get_current_task_id, resolve_safe_path, get_current_files_dir
from app import database as db

# Module-level task_id for context
_current_task_id: Optional[str] = None


def set_diff_task_id(task_id: str):
    """Set the current task ID for diff operations."""
    global _current_task_id
    _current_task_id = task_id


def get_diff_task_id() -> str:
    return _current_task_id or get_current_task_id()


def generate_unified_diff(old_content: str, new_content: str, path: str) -> str:
    """Generate a unified diff between old and new content."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{path}", tofile=f"b/{path}", lineterm="",
    )
    return "\n".join(diff)


def get_file_diff(path: str, new_content: str) -> dict:
    """Generate a diff showing what would change if new_content is written."""
    task_id = get_diff_task_id()
    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    try:
        old_content = ""
        is_new_file = True
        if file_path.exists() and file_path.is_file():
            old_content = file_path.read_text(encoding="utf-8")
            is_new_file = False

        diff = generate_unified_diff(old_content, new_content, path)
        return {
            "success": True,
            "path": path,
            "is_new_file": is_new_file,
            "diff": diff,
            "old_content": old_content,
            "new_content": new_content,
            "lines_added": sum(1 for l in diff.split("\n") if l.startswith("+") and not l.startswith("+++")),
            "lines_removed": sum(1 for l in diff.split("\n") if l.startswith("-") and not l.startswith("---")),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def preview_file_change(path: str, new_content: str) -> dict:
    """Create a pending file change with diff."""
    import config

    diff_result = get_file_diff(path, new_content)
    if not diff_result.get("success"):
        return diff_result

    change_id = str(uuid.uuid4())[:12]
    task_id = get_diff_task_id()

    status = "pending" if config.EXECUTION_MODE == "safe" else "applied"
    db.create_file_change(
        change_id=change_id,
        task_id=task_id,
        path=path,
        old_content=diff_result["old_content"],
        new_content=new_content,
        diff=diff_result["diff"],
        status=status,
    )

    if config.EXECUTION_MODE != "safe":
        db.mark_file_change_applied(change_id)

    return {
        "success": True,
        "change_id": change_id,
        "path": path,
        "status": status,
        "diff": diff_result["diff"],
        "lines_added": diff_result["lines_added"],
        "lines_removed": diff_result["lines_removed"],
    }


def accept_file_change(change_id: str) -> dict:
    """Accept a pending file change."""
    change = db.get_file_change(change_id)
    if not change:
        return {"success": False, "error": f"Change not found: {change_id}"}
    if change["status"] != "pending":
        return {"success": False, "error": f"Change not pending (status: {change['status']})"}

    # Write to disk
    task_id = change["task_id"]
    path = change["path"]
    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(change["new_content"], encoding="utf-8")
    except Exception as e:
        return {"success": False, "error": str(e)}

    db.accept_file_change(change_id)
    db.mark_file_change_applied(change_id)
    artifact_id = str(uuid.uuid4())[:12]
    db.create_artifact(
        artifact_id=artifact_id,
        task_id=task_id,
        artifact_type="file",
        name=Path(path).name,
        path=path,
        mime_type=_guess_mime(file_path.suffix.lower()),
        size=len(change["new_content"]),
    )
    return {
        "success": True,
        "change_id": change_id,
        "path": path,
        "status": "applied",
        "artifact_id": artifact_id,
    }


def reject_file_change(change_id: str) -> dict:
    """Reject a pending file change."""
    change = db.get_file_change(change_id)
    if not change:
        return {"success": False, "error": f"Change not found: {change_id}"}
    if change["status"] != "pending":
        return {"success": False, "error": f"Change not pending (status: {change['status']})"}

    db.reject_file_change(change_id)
    return {"success": True, "change_id": change_id, "path": change["path"], "status": "rejected"}


def apply_file_patch(path: str, patch: str) -> dict:
    """Apply a unified diff patch to a file."""
    task_id = get_diff_task_id()
    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}
    if not file_path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    try:
        new_lines = []
        in_hunk = False
        for line in patch.split("\n"):
            if line.startswith("@@"):
                in_hunk = True
                continue
            if not in_hunk:
                continue
            if line.startswith("-"):
                continue
            elif line.startswith("+"):
                new_lines.append(line[1:])
            else:
                new_lines.append(line[1:] if line.startswith(" ") else line)

        file_path.write_text("\n".join(new_lines), encoding="utf-8")
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_pending_changes(task_id: Optional[str] = None) -> list[dict]:
    """List all pending file changes."""
    tid = task_id or get_diff_task_id()
    changes = db.list_file_changes(task_id=tid, status="pending")
    return [
        {"id": c["id"], "task_id": c["task_id"], "path": c["path"], "status": c["status"], "diff": c["diff"], "created_at": c["created_at"]}
        for c in changes
    ]


def _guess_mime(ext: str) -> str:
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
