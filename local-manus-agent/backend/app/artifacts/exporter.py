"""Task Exporter - creates ZIP archives of task outputs."""
import json
import time
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

from app.workspace.manager import get_task_workspace, get_files_dir, get_screenshots_dir
from app import database as db

# Files/patterns to exclude from export
EXCLUDED_PATTERNS = [".env", ".sqlite", ".db", "node_modules", ".next", "__pycache__", ".git"]


def create_task_export(task_id: str) -> dict:
    """Create a ZIP export of a task's workspace and metadata.

    Args:
        task_id: Task identifier.

    Returns:
        Dict with success, zip_path, size, artifact_id.
    """
    task = db.get_task(task_id)
    if not task:
        return {"success": False, "error": "Task not found"}

    task_ws = get_task_workspace(task_id)
    if not task_ws.exists():
        return {"success": False, "error": "Task workspace not found"}

    # Build ZIP in memory then write to artifacts dir
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. summary.md
        summary = build_summary_md(task_id, task)
        zf.writestr("summary.md", summary)

        # 2. metadata.json
        metadata = _build_metadata(task_id, task)
        zf.writestr("metadata.json", json.dumps(metadata, indent=2, default=str))

        # 3. files/
        files_dir = get_files_dir(task_id)
        if files_dir.exists():
            for f in sorted(files_dir.rglob("*")):
                if f.is_file() and not _is_excluded(f, files_dir):
                    rel = f.relative_to(files_dir)
                    zf.writestr(f"files/{rel}", f.read_bytes())

        # 4. screenshots/
        ss_dir = get_screenshots_dir(task_id)
        if ss_dir.exists():
            for f in sorted(ss_dir.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(ss_dir)
                    zf.writestr(f"screenshots/{rel}", f.read_bytes())

        # 5. logs/ (agent steps as JSON)
        steps = task.get("plan_steps", [])
        if steps:
            zf.writestr("logs/agent_steps.json", json.dumps(steps, indent=2, default=str))

        tool_logs = task.get("tool_logs", [])
        if tool_logs:
            zf.writestr("logs/tool_logs.json", json.dumps(tool_logs, indent=2, default=str))

    # Write ZIP to task workspace
    zip_bytes = zip_buffer.getvalue()
    export_dir = task_ws / "artifacts"
    export_dir.mkdir(exist_ok=True)
    zip_filename = f"task-{task_id[:8]}.zip"
    zip_path = export_dir / zip_filename
    zip_path.write_bytes(zip_bytes)

    # Register as artifact
    artifact_id = str(uuid.uuid4())[:12]
    db.create_artifact(
        artifact_id=artifact_id,
        task_id=task_id,
        artifact_type="archive",
        name=zip_filename,
        path=f"artifacts/{zip_filename}",
        mime_type="application/zip",
        size=len(zip_bytes),
    )

    return {
        "success": True,
        "task_id": task_id,
        "artifact_id": artifact_id,
        "filename": zip_filename,
        "size": len(zip_bytes),
        "path": str(zip_path),
    }


def build_summary_md(task_id: str, task: Optional[dict] = None) -> str:
    """Build a markdown summary of the task."""
    if not task:
        task = db.get_task(task_id) or {}

    lines = [
        f"# Task Export: {task_id}",
        "",
        f"**Prompt:** {task.get('message', 'N/A')}",
        f"**Created:** {_format_time(task.get('created_at', 0))}",
        f"**Status:** {task.get('status', 'unknown')}",
        f"**Mode:** {task.get('mode', 'safe')}",
        f"**Summary:** {task.get('summary', 'N/A')}",
        "",
        "## Files Created",
        "",
    ]

    for f in task.get("created_files", []):
        lines.append(f"- `{f.get('path', '')}` ({f.get('size', 0)} bytes)")

    lines.extend(["", "## Artifacts", ""])
    for a in db.list_artifacts(task_id=task_id):
        lines.append(f"- [{a.get('type', '')}] {a.get('name', '')} ({a.get('size', 0)} bytes)")

    lines.extend(["", "## Agent Steps", ""])
    for s in task.get("plan_steps", []):
        status_icon = "✓" if s.get("status") == "done" else "✗" if s.get("status") == "error" else "○"
        lines.append(f"- {status_icon} {s.get('description', '')} (`{s.get('tool', '')}`)")

    return "\n".join(lines)


def collect_task_files(task_id: str) -> list[dict]:
    """List files that would be included in export."""
    files_dir = get_files_dir(task_id)
    if not files_dir.exists():
        return []

    result = []
    for f in sorted(files_dir.rglob("*")):
        if f.is_file() and not _is_excluded(f, files_dir):
            result.append({
                "path": str(f.relative_to(files_dir)),
                "size": f.stat().st_size,
            })
    return result


def _build_metadata(task_id: str, task: dict) -> dict:
    """Build metadata.json content."""
    return {
        "task_id": task_id,
        "message": task.get("message", ""),
        "status": task.get("status", ""),
        "mode": task.get("mode", ""),
        "created_at": task.get("created_at", 0),
        "completed_at": task.get("completed_at"),
        "summary": task.get("summary", ""),
        "artifacts": db.list_artifacts(task_id=task_id),
        "created_files": task.get("created_files", []),
        "plan_steps_count": len(task.get("plan_steps", [])),
        "tool_logs_count": len(task.get("tool_logs", [])),
        "exported_at": time.time(),
        "version": "1.0.0",
    }


def _is_excluded(file_path: Path, base_dir: Path) -> bool:
    """Check if a file should be excluded from export."""
    rel = str(file_path.relative_to(base_dir)).replace("\\", "/")
    for pattern in EXCLUDED_PATTERNS:
        if pattern in rel:
            return True
    # Skip large files (>10MB)
    if file_path.stat().st_size > 10_000_000:
        return True
    return False


def _format_time(ts: float) -> str:
    """Format a timestamp."""
    if not ts:
        return "N/A"
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
