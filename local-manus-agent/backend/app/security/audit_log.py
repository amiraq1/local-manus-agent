"""Security Audit Log - records all security-relevant events."""
import time
import uuid
import json
from typing import Optional


def _get_db():
    from app.database import get_db
    return get_db()


def init_security_tables():
    """Create security events table."""
    from app.database import get_db
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS security_events (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                decision TEXT NOT NULL,
                reason TEXT,
                metadata TEXT,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_security_events_task ON security_events(task_id);
            CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
        """)


def log_security_event(
    task_id: Optional[str],
    event_type: str,
    severity: str,
    action: str,
    target: Optional[str],
    decision: str,
    reason: str,
    metadata: Optional[dict] = None,
):
    """Log a security event.

    Args:
        task_id: Task identifier (optional).
        event_type: file_access, command, network, browser, auth.
        severity: low, medium, high, critical.
        action: What was attempted.
        target: Path/URL/command that was targeted.
        decision: allow, deny, require_approval.
        reason: Why the decision was made.
        metadata: Additional context.
    """
    # Only log medium+ severity to avoid flooding
    if severity == "low":
        return

    event_id = str(uuid.uuid4())[:12]
    meta_json = json.dumps(metadata) if metadata else None

    try:
        from app.database import get_db
        with get_db() as conn:
            conn.execute(
                "INSERT INTO security_events (id, task_id, event_type, severity, action, target, decision, reason, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event_id, task_id, event_type, severity, action, target, decision, reason, meta_json, time.time()),
            )
    except Exception:
        pass  # Don't crash on logging failure


def get_security_events(task_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    """Get recent security events."""
    from app.database import get_db
    query = "SELECT * FROM security_events"
    params = []
    if task_id:
        query += " WHERE task_id=?"
        params.append(task_id)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


# Initialize on import
init_security_tables()
