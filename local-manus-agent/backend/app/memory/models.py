"""Data models for the memory system."""
from dataclasses import dataclass, field
from typing import Optional


MEMORY_TYPES = ["user_preference", "project_summary", "decision", "error", "fix", "note"]

# File patterns to skip during indexing
SKIP_PATTERNS = [
    ".env", ".git", "node_modules", ".next", "__pycache__",
    ".pyc", ".db", ".sqlite", ".lock", ".log",
    "package-lock.json", "yarn.lock",
]

# Binary extensions to skip
BINARY_EXTENSIONS = [
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar",
    ".pdf", ".doc", ".docx",
    ".exe", ".dll", ".so", ".dylib",
    ".mp3", ".mp4", ".wav", ".avi",
]

# Max file size to index (100KB)
MAX_INDEX_SIZE = 100_000

# Language detection by extension
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".html": "html", ".htm": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml", ".yml": "yaml",
    ".sh": "shell", ".bash": "shell",
    ".sql": "sql",
    ".txt": "text",
}


@dataclass
class FileIndexEntry:
    """Represents an indexed file."""
    id: str
    task_id: str
    path: str
    content_hash: str
    summary: str
    language: str
    symbols: list[str] = field(default_factory=list)


@dataclass
class Memory:
    """Represents a stored memory."""
    id: str
    task_id: Optional[str]
    type: str
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""
    path: str
    score: float
    snippet: str
    language: str
