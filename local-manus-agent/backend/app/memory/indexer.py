"""File Indexer - scans task workspace and builds a searchable index."""
import hashlib
import re
from pathlib import Path
from typing import Optional

from app.workspace.manager import get_files_dir
from app.memory.models import SKIP_PATTERNS, BINARY_EXTENSIONS, MAX_INDEX_SIZE, LANGUAGE_MAP
from app.memory.memory_store import upsert_file_index, clear_file_index, get_file_index


def index_task_files(task_id: str, force: bool = False) -> dict:
    """Index all files in a task's workspace.

    Skips binary files, large files, and sensitive patterns.

    Args:
        task_id: Task identifier.
        force: If True, re-index all files regardless of hash.

    Returns:
        Dict with indexing results.
    """
    files_dir = get_files_dir(task_id)
    if not files_dir.exists():
        return {"success": False, "error": "Task workspace not found"}

    if force:
        clear_file_index(task_id)

    existing = {e["path"]: e["content_hash"] for e in get_file_index(task_id)}
    indexed = 0
    skipped = 0
    errors = []

    for file_path in sorted(files_dir.rglob("*")):
        if not file_path.is_file():
            continue

        rel_path = str(file_path.relative_to(files_dir)).replace("\\", "/")

        # Skip patterns
        if _should_skip(rel_path, file_path):
            skipped += 1
            continue

        # Check size
        try:
            size = file_path.stat().st_size
            if size > MAX_INDEX_SIZE:
                skipped += 1
                continue
        except OSError:
            skipped += 1
            continue

        # Read and hash
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            content_hash = hashlib.md5(content.encode()).hexdigest()
        except Exception as e:
            errors.append(f"{rel_path}: {e}")
            continue

        # Skip if unchanged
        if not force and rel_path in existing and existing[rel_path] == content_hash:
            skipped += 1
            continue

        # Extract metadata
        language = _detect_language(file_path)
        summary = _generate_summary(content, language, rel_path)
        symbols = _extract_symbols(content, language)

        upsert_file_index(task_id, rel_path, content_hash, summary, language, symbols)
        indexed += 1

    return {
        "success": True,
        "task_id": task_id,
        "indexed": indexed,
        "skipped": skipped,
        "errors": errors,
        "total_in_index": len(get_file_index(task_id)),
    }


def _should_skip(rel_path: str, file_path: Path) -> bool:
    """Check if a file should be skipped during indexing."""
    # Check extension
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    # Check path patterns
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        for pattern in SKIP_PATTERNS:
            if pattern in part:
                return True

    return False


def _detect_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    return LANGUAGE_MAP.get(file_path.suffix.lower(), "unknown")


def _generate_summary(content: str, language: str, path: str) -> str:
    """Generate a brief summary of file content."""
    lines = content.strip().split("\n")
    total_lines = len(lines)

    if language == "html":
        # Extract title
        title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
        title = title_match.group(1) if title_match else "Untitled"
        headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", content, re.IGNORECASE)
        return f"HTML: {title}. {total_lines} lines. Headings: {', '.join(headings[:3]) or 'none'}"

    elif language == "css":
        classes = re.findall(r"\.([\w-]+)\s*\{", content)
        return f"CSS: {total_lines} lines, {len(classes)} classes. Top: {', '.join(classes[:5])}"

    elif language in ("javascript", "typescript"):
        funcs = re.findall(r"(?:function|const|let|var)\s+(\w+)", content)
        return f"{language}: {total_lines} lines, {len(funcs)} declarations. Top: {', '.join(funcs[:5])}"

    elif language == "python":
        funcs = re.findall(r"(?:def|class)\s+(\w+)", content)
        return f"Python: {total_lines} lines, {len(funcs)} definitions. Top: {', '.join(funcs[:5])}"

    elif language == "json":
        try:
            import json
            data = json.loads(content)
            keys = list(data.keys())[:5] if isinstance(data, dict) else []
            return f"JSON: {total_lines} lines. Keys: {', '.join(keys)}"
        except Exception:
            return f"JSON: {total_lines} lines"

    else:
        first_line = lines[0][:80] if lines else ""
        return f"{path}: {total_lines} lines. First: {first_line}"


def _extract_symbols(content: str, language: str) -> list[str]:
    """Extract symbol names from file content."""
    symbols = []

    if language == "python":
        symbols = re.findall(r"(?:def|class)\s+(\w+)", content)

    elif language in ("javascript", "typescript"):
        # Functions and components
        symbols = re.findall(r"(?:function|const|let|export\s+(?:default\s+)?(?:function|class))\s+(\w+)", content)
        # React components (PascalCase exports)
        symbols += re.findall(r"export\s+(?:default\s+)?(\w+)", content)

    elif language == "html":
        # Title and headings
        titles = re.findall(r"<title>(.*?)</title>", content, re.IGNORECASE)
        headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", content, re.IGNORECASE)
        symbols = titles + headings

    elif language == "css":
        # Class names
        symbols = re.findall(r"\.([\w-]+)\s*\{", content)

    # Deduplicate and limit
    seen = set()
    unique = []
    for s in symbols:
        s = s.strip()
        if s and s not in seen and len(s) > 1:
            seen.add(s)
            unique.append(s)
    return unique[:30]
