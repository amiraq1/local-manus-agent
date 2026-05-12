"""SQLite database module for persisting tasks, messages, and logs."""
import sqlite3
import json
import time
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from config import BASE_DIR

DB_PATH = BASE_DIR / "manus_agent.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                mode TEXT NOT NULL DEFAULT 'safe',
                created_at REAL NOT NULL,
                completed_at REAL,
                summary TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                phase TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS plan_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                step_index INTEGER NOT NULL,
                description TEXT NOT NULL,
                tool TEXT NOT NULL,
                params TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS tool_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                step_index INTEGER,
                tool TEXT NOT NULL,
                params TEXT,
                success INTEGER NOT NULL DEFAULT 0,
                result TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS created_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                path TEXT NOT NULL,
                size INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS pending_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                command TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL,
                resolved_at REAL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_task ON messages(task_id);
            CREATE INDEX IF NOT EXISTS idx_plan_steps_task ON plan_steps(task_id);
            CREATE INDEX IF NOT EXISTS idx_tool_logs_task ON tool_logs(task_id);
            CREATE INDEX IF NOT EXISTS idx_created_files_task ON created_files(task_id);
            CREATE INDEX IF NOT EXISTS idx_pending_approvals_task ON pending_approvals(task_id, status);

            CREATE TABLE IF NOT EXISTS browser_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                action TEXT NOT NULL,
                url TEXT,
                selector TEXT,
                result TEXT,
                screenshot_path TEXT,
                success INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_browser_logs_task ON browser_logs(task_id);

            CREATE TABLE IF NOT EXISTS file_changes (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                path TEXT NOT NULL,
                old_content TEXT,
                new_content TEXT,
                diff TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL,
                resolved_at REAL
            );

            CREATE INDEX IF NOT EXISTS idx_file_changes_task ON file_changes(task_id);
            CREATE INDEX IF NOT EXISTS idx_file_changes_status ON file_changes(status);

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                mime_type TEXT,
                size INTEGER DEFAULT 0,
                metadata TEXT,
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_artifacts_task ON artifacts(task_id);
            CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);

            CREATE TABLE IF NOT EXISTS agent_steps (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                phase TEXT NOT NULL,
                input_summary TEXT,
                output_summary TEXT,
                status TEXT,
                created_at REAL
            );

            CREATE INDEX IF NOT EXISTS idx_agent_steps_task ON agent_steps(task_id);
        """)


# --- Task CRUD ---

def create_task(task_id: str, message: str, mode: str = "safe") -> dict:
    """Create a new task record."""
    now = time.time()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO tasks (id, message, status, mode, created_at) VALUES (?, ?, 'running', ?, ?)",
            (task_id, message, mode, now),
        )
    return {"id": task_id, "message": message, "status": "running", "mode": mode, "created_at": now}


def update_task_status(task_id: str, status: str, summary: Optional[str] = None):
    """Update task status."""
    with get_db() as conn:
        if summary:
            conn.execute(
                "UPDATE tasks SET status=?, summary=?, completed_at=? WHERE id=?",
                (status, summary, time.time(), task_id),
            )
        else:
            conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))


def get_task(task_id: str) -> Optional[dict]:
    """Get a single task with all related data."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return None

        task = dict(row)

        # Get messages
        messages = conn.execute(
            "SELECT * FROM messages WHERE task_id=? ORDER BY created_at", (task_id,)
        ).fetchall()
        task["messages"] = [dict(m) for m in messages]

        # Get plan steps
        steps = conn.execute(
            "SELECT * FROM plan_steps WHERE task_id=? ORDER BY step_index", (task_id,)
        ).fetchall()
        task["plan_steps"] = [dict(s) for s in steps]

        # Get tool logs
        logs = conn.execute(
            "SELECT * FROM tool_logs WHERE task_id=? ORDER BY created_at", (task_id,)
        ).fetchall()
        task["tool_logs"] = [dict(l) for l in logs]

        # Get created files
        files = conn.execute(
            "SELECT * FROM created_files WHERE task_id=? ORDER BY created_at", (task_id,)
        ).fetchall()
        task["created_files"] = [dict(f) for f in files]

        # Get browser logs
        browser = conn.execute(
            "SELECT * FROM browser_logs WHERE task_id=? ORDER BY created_at", (task_id,)
        ).fetchall()
        task["browser_logs"] = [dict(b) for b in browser]

        # Get file changes
        changes = conn.execute(
            "SELECT * FROM file_changes WHERE task_id=? ORDER BY created_at", (task_id,)
        ).fetchall()
        task["file_changes"] = [dict(c) for c in changes]

        return task


def get_all_tasks() -> list[dict]:
    """Get all tasks (summary only)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, message, status, mode, created_at, completed_at, summary FROM tasks ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# --- Messages ---

def add_message(task_id: str, role: str, content: str, phase: Optional[str] = None):
    """Add a message to a task."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (task_id, role, content, phase, created_at) VALUES (?, ?, ?, ?, ?)",
            (task_id, role, content, phase, time.time()),
        )


# --- Plan Steps ---

def save_plan_steps(task_id: str, steps: list[dict]):
    """Save plan steps for a task."""
    now = time.time()
    with get_db() as conn:
        for i, step in enumerate(steps):
            conn.execute(
                "INSERT INTO plan_steps (task_id, step_index, description, tool, params, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                (task_id, i, step.get("description", ""), step.get("tool", ""), json.dumps(step.get("params", {})), now),
            )


def update_step_status(task_id: str, step_index: int, status: str, result: Optional[str] = None):
    """Update a plan step status."""
    with get_db() as conn:
        conn.execute(
            "UPDATE plan_steps SET status=?, result=? WHERE task_id=? AND step_index=?",
            (status, result, task_id, step_index),
        )


# --- Tool Logs ---

def add_tool_log(task_id: str, step_index: int, tool: str, params: dict, success: bool, result: Optional[str] = None):
    """Add a tool log entry."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO tool_logs (task_id, step_index, tool, params, success, result, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, step_index, tool, json.dumps(params), 1 if success else 0, result, time.time()),
        )


# --- Created Files ---

def add_created_file(task_id: str, path: str, size: int = 0):
    """Record a file created by a task."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO created_files (task_id, path, size, created_at) VALUES (?, ?, ?, ?)",
            (task_id, path, size, time.time()),
        )


# --- Pending Approvals ---

def create_approval(task_id: str, command: str) -> int:
    """Create a pending approval for a command."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO pending_approvals (task_id, command, status, created_at) VALUES (?, ?, 'pending', ?)",
            (task_id, command, time.time()),
        )
        return cursor.lastrowid


def resolve_approval(approval_id: int, approved: bool):
    """Resolve a pending approval."""
    status = "approved" if approved else "rejected"
    with get_db() as conn:
        conn.execute(
            "UPDATE pending_approvals SET status=?, resolved_at=? WHERE id=?",
            (status, time.time(), approval_id),
        )


def get_pending_approvals(task_id: Optional[str] = None) -> list[dict]:
    """Get pending approvals, optionally filtered by task."""
    with get_db() as conn:
        if task_id:
            rows = conn.execute(
                "SELECT * FROM pending_approvals WHERE task_id=? AND status='pending' ORDER BY created_at",
                (task_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM pending_approvals WHERE status='pending' ORDER BY created_at"
            ).fetchall()
        return [dict(r) for r in rows]


def get_approval(approval_id: int) -> Optional[dict]:
    """Get a single approval by ID."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM pending_approvals WHERE id=?", (approval_id,)).fetchone()
        return dict(row) if row else None


# --- Browser Logs ---

def add_browser_log(
    task_id: str,
    action: str,
    url: Optional[str] = None,
    selector: Optional[str] = None,
    result: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    success: bool = True,
):
    """Add a browser action log entry."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO browser_logs (task_id, action, url, selector, result, screenshot_path, success, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, action, url, selector, result, screenshot_path, 1 if success else 0, time.time()),
        )


def get_browser_logs(task_id: str) -> list[dict]:
    """Get browser logs for a task."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM browser_logs WHERE task_id=? ORDER BY created_at", (task_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# --- File Changes ---

def create_file_change(
    change_id: str,
    task_id: str,
    path: str,
    old_content: Optional[str],
    new_content: str,
    diff: str,
    status: str = "pending",
) -> dict:
    """Create a file change record."""
    now = time.time()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO file_changes (id, task_id, path, old_content, new_content, diff, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (change_id, task_id, path, old_content, new_content, diff, status, now),
        )
    return {
        "id": change_id,
        "task_id": task_id,
        "path": path,
        "status": status,
        "created_at": now,
    }


def get_file_change(change_id: str) -> Optional[dict]:
    """Get a file change by ID."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM file_changes WHERE id=?", (change_id,)).fetchone()
        return dict(row) if row else None


def list_file_changes(task_id: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    """List file changes, optionally filtered by task_id and/or status."""
    query = "SELECT * FROM file_changes WHERE 1=1"
    params = []
    if task_id:
        query += " AND task_id=?"
        params.append(task_id)
    if status:
        query += " AND status=?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def update_file_change_status(change_id: str, status: str):
    """Update the status of a file change."""
    with get_db() as conn:
        conn.execute(
            "UPDATE file_changes SET status=?, resolved_at=? WHERE id=?",
            (status, time.time(), change_id),
        )


def accept_file_change(change_id: str):
    """Mark a file change as accepted."""
    update_file_change_status(change_id, "accepted")


def reject_file_change(change_id: str):
    """Mark a file change as rejected."""
    update_file_change_status(change_id, "rejected")


def mark_file_change_applied(change_id: str):
    """Mark a file change as applied to disk."""
    update_file_change_status(change_id, "applied")


# --- Artifacts ---

def create_artifact(
    artifact_id: str,
    task_id: str,
    artifact_type: str,
    name: str,
    path: str,
    mime_type: Optional[str] = None,
    size: int = 0,
    metadata: Optional[str] = None,
) -> dict:
    """Create an artifact record."""
    now = time.time()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO artifacts (id, task_id, type, name, path, mime_type, size, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (artifact_id, task_id, artifact_type, name, path, mime_type, size, metadata, now),
        )
    return {"id": artifact_id, "task_id": task_id, "type": artifact_type, "name": name, "path": path, "size": size, "created_at": now}


def list_artifacts(task_id: Optional[str] = None, artifact_type: Optional[str] = None) -> list[dict]:
    """List artifacts, optionally filtered."""
    query = "SELECT * FROM artifacts WHERE 1=1"
    params = []
    if task_id:
        query += " AND task_id=?"
        params.append(task_id)
    if artifact_type:
        query += " AND type=?"
        params.append(artifact_type)
    query += " ORDER BY created_at DESC"
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_artifact(artifact_id: str) -> Optional[dict]:
    """Get a single artifact by ID."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
        return dict(row) if row else None


def delete_artifact(artifact_id: str) -> bool:
    """Delete an artifact record."""
    with get_db() as conn:
        conn.execute("DELETE FROM artifacts WHERE id=?", (artifact_id,))
        return True


# Initialize on import
init_db()
