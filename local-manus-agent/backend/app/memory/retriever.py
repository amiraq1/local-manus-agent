"""Retriever - searches indexed files and retrieves relevant context."""
import re
from typing import Optional

from app.workspace.manager import get_files_dir, resolve_safe_path
from app.memory.memory_store import get_file_index, log_retrieval, list_memories
from app.memory.models import RetrievalResult


def search_project_files(task_id: str, query: str) -> dict:
    """Search indexed files for a query string.

    Uses simple keyword matching against file summaries, symbols, and content.

    Args:
        task_id: Task identifier.
        query: Search query.

    Returns:
        Dict with matching files and snippets.
    """
    if not query.strip():
        return {"success": False, "error": "Query is empty"}

    index = get_file_index(task_id)
    if not index:
        return {"success": True, "results": [], "message": "No files indexed. Run index first."}

    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))
    results = []

    for entry in index:
        score = 0.0
        snippet = ""

        # Match in path
        if query_lower in entry["path"].lower():
            score += 3.0

        # Match in summary
        summary = (entry.get("summary") or "").lower()
        for word in query_words:
            if word in summary:
                score += 1.0

        # Match in symbols
        symbols = entry.get("symbols", [])
        if isinstance(symbols, str):
            import json
            try:
                symbols = json.loads(symbols)
            except Exception:
                symbols = []
        for sym in symbols:
            if query_lower in sym.lower():
                score += 2.0
                break

        # If score > 0, try to find snippet in actual file
        if score > 0:
            snippet = _find_snippet(task_id, entry["path"], query)
            if snippet:
                score += 1.0

            results.append({
                "path": entry["path"],
                "score": score,
                "language": entry.get("language", "unknown"),
                "summary": entry.get("summary", ""),
                "snippet": snippet,
                "symbols": symbols[:10],
            })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:10]

    # Log retrieval
    log_retrieval(task_id, query, results)

    return {"success": True, "query": query, "results": results, "total": len(results)}


def get_relevant_context(task_id: str, query: str, limit: int = 5) -> dict:
    """Get relevant context for a query - combines file search and memories.

    Args:
        task_id: Task identifier.
        query: The user's message or task description.
        limit: Max results to return.

    Returns:
        Dict with context items for the agent.
    """
    context_items = []

    # Search files
    search_result = search_project_files(task_id, query)
    if search_result.get("success"):
        for r in search_result.get("results", [])[:limit]:
            context_items.append({
                "type": "file",
                "path": r["path"],
                "summary": r["summary"],
                "snippet": r.get("snippet", ""),
                "relevance": r["score"],
            })

    # Search memories
    memories = list_memories(task_id=task_id)
    query_lower = query.lower()
    for mem in memories[:20]:
        content_lower = mem.get("content", "").lower()
        if any(w in content_lower for w in re.findall(r"\w+", query_lower)):
            context_items.append({
                "type": "memory",
                "memory_type": mem["type"],
                "content": mem["content"][:200],
                "relevance": 1.0,
            })

    # Sort by relevance and limit
    context_items.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    context_items = context_items[:limit]

    return {
        "success": True,
        "task_id": task_id,
        "query": query,
        "context": context_items,
        "total": len(context_items),
    }


def _find_snippet(task_id: str, path: str, query: str, context_lines: int = 2) -> str:
    """Find a relevant snippet in a file matching the query."""
    safe, file_path, _ = resolve_safe_path(task_id, path, "files")
    if not safe or not file_path.exists():
        return ""

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        query_lower = query.lower()

        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet = "\n".join(lines[start:end])
                return snippet[:300]

        return ""
    except Exception:
        return ""
