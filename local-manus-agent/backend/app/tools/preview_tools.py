"""Preview server tools - serves files from the current task's workspace."""
import subprocess
import sys
from typing import Optional

from app.workspace.manager import get_current_task_id, get_files_dir
from config import PREVIEW_PORT, PREVIEW_HOST

_preview_process: Optional[subprocess.Popen] = None
_preview_task_id: Optional[str] = None


def start_preview() -> dict:
    """Start a local HTTP preview server serving the current task's files."""
    global _preview_process, _preview_task_id

    if _preview_process is not None and _preview_process.poll() is None:
        return {
            "success": True,
            "message": "Preview server already running",
            "url": f"http://{PREVIEW_HOST}:{PREVIEW_PORT}",
            "task_id": _preview_task_id,
        }

    task_id = get_current_task_id()
    files_dir = get_files_dir(task_id)
    files_dir.mkdir(parents=True, exist_ok=True)

    try:
        _preview_process = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(PREVIEW_PORT), "--bind", PREVIEW_HOST],
            cwd=str(files_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _preview_task_id = task_id

        return {
            "success": True,
            "message": "Preview server started",
            "url": f"http://{PREVIEW_HOST}:{PREVIEW_PORT}",
            "task_id": task_id,
            "pid": _preview_process.pid,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_preview() -> dict:
    """Stop the running preview server."""
    global _preview_process, _preview_task_id

    if _preview_process is None:
        return {"success": True, "message": "No preview server running"}

    try:
        _preview_process.terminate()
        _preview_process.wait(timeout=5)
        _preview_process = None
        _preview_task_id = None
        return {"success": True, "message": "Preview server stopped"}
    except subprocess.TimeoutExpired:
        _preview_process.kill()
        _preview_process = None
        _preview_task_id = None
        return {"success": True, "message": "Preview server force-killed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_preview_url() -> dict:
    """Get the current preview server URL and status."""
    global _preview_process

    is_running = _preview_process is not None and _preview_process.poll() is None
    return {
        "running": is_running,
        "url": f"http://{PREVIEW_HOST}:{PREVIEW_PORT}" if is_running else None,
        "task_id": _preview_task_id,
    }
