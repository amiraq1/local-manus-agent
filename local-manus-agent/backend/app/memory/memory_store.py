"""Memory Store - persists and retrieves agent memories and file index."""
import json
import time
import uuid
import hashlib
from typing import Optional

from app.memory.models import MEMORY_TYPES


def _get_db():
    """Get database connection (import here to avoid circular imports)."""
    from app.database import get_db
    return get_db()


def init_memory_tables():
    """Create memory tables if they don't exist."""
    from app.database import get_db
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memories_task ON memories(task_id);
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);

            CREATE TABLE IF NOT EXISTS file_index (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                path TEXT NOT NULL,
                content_hash TEXT,
                summary TEXT,
                language TEXT,
                symbols TEXT,
                updated_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_file_index_task ON file_index(task_id);
            CREATE INDEX IF NOT EXISTS idx_file_index_path ON file_index(task_id, path);

            CREATE TABLE IF NOT EXISTS retrieval_logs (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                query TEXT NOT NULL,
                results TEXT,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_retrieval_logs_task ON retrieval_logs(task_id);
        """)


# --- Memories CRUD ---

def remember(task_id: Optional[str], memory_type: str, content: str, metadata: Optional[dict] = None) -> dict:
    """Store a memory."""
    if memory_type not in MEMORY_TYPES:
        return {"success": False, "error": f"Invalid type. Use: {MEMORY_TYPES}"}

    mem_id = str(uuid.uuid4())[:12]
    meta_json = json.dumps(metadata) if metadata else None

    from app.database import get_db
    with get_db() as conn:
        conn.execute(
            "INSERT INTO memories (id, task_id, type, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (mem_id, task_id, memory_type, content, meta_json, time.time()),
        )
    return {"success": True, "id": mem_id, "type": memory_type}


def list_memories(task_id: Optional[str] = None, memory_type: Optional[str] = None) -> list[dict]:
    """List memories, optionally filtered."""
    query = "SELECT * FROM memories WHERE 1=1"
    params = []
    if task_id:
        query += " AND task_id=?"
        params.append(task_id)
    if memory_type:
        query += " AND type=?"
        params.append(memory_type)
    query += " ORDER BY created_at DESC"

    from app.database import get_db
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except Exception:
                    pass
            results.append(d)
        return results


def get_memory(memory_id: str) -> Optional[dict]:
    """Get a single memory."""
    from app.database import get_db
    with get_db() as conn:
        row = conn.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
        if row:
            d = dict(row)
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except Exception:
                    pass
            return d
        return None


# --- File Index CRUD ---

def upsert_file_index(task_id: str, path: str, content_hash: str, summary: str, language: str, symbols: list[str]) -> str:
    """Insert or update a file index entry."""
    from app.database import get_db

    entry_id = hashlib.md5(f"{task_id}:{path}".encode()).hexdigest()[:12]
    symbols_json = json.dumps(symbols)

    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO file_index (id, task_id, path, content_hash, summary, language, symbols, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, task_id, path, content_hash, summary, language, symbols_json, time.time()))

    return entry_id


def get_file_index(task_id: str) -> list[dict]:
    """Get all indexed files for a task."""
    from app.database import get_db
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM file_index WHERE task_id=? ORDER BY path", (task_id,)
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("symbols"):
                try:
                    d["symbols"] = json.loads(d["symbols"])
                except Exception:
                    d["symbols"] = []
            results.append(d)
        return results


def clear_file_index(task_id: str):
    """Clear file index for a task."""
    from app.database import get_db
    with get_db() as conn:
        conn.execute("DELETE FROM file_index WHERE task_id=?", (task_id,))


# --- Retrieval Logs ---

def log_retrieval(task_id: str, query: str, results: list[dict]):
    """Log a retrieval query and results."""
    from app.database import get_db
    log_id = str(uuid.uuid4())[:12]
    with get_db() as conn:
        conn.execute(
            "INSERT INTO retrieval_logs (id, task_id, query, results, created_at) VALUES (?, ?, ?, ?, ?)",
            (log_id, task_id, query, json.dumps(results, default=str)[:5000], time.time()),
        )


# Initialize tables on import
init_memory_tables()
