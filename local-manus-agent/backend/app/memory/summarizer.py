"""Summarizer - generates project summaries from indexed files."""
import uuid
from typing import Optional

from app.memory.memory_store import get_file_index, remember
from app.workspace.manager import get_files_dir
from app import database as db


def summarize_project(task_id: str) -> dict:
    """Generate a summary of the project in a task workspace.

    Creates a structured summary from the file index and stores it
    as both a memory and an artifact.

    Args:
        task_id: Task identifier.

    Returns:
        Dict with project summary.
    """
    index = get_file_index(task_id)
    files_dir = get_files_dir(task_id)

    if not index:
        return {"success": False, "error": "No files indexed. Run index first."}

    # Analyze project structure
    languages = {}
    all_symbols = []
    total_lines = 0
    file_types = {}

    for entry in index:
        lang = entry.get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1

        symbols = entry.get("symbols", [])
        if isinstance(symbols, str):
            import json
            try:
                symbols = json.loads(symbols)
            except Exception:
                symbols = []
        all_symbols.extend(symbols[:5])

        ext = "." + entry["path"].rsplit(".", 1)[-1] if "." in entry["path"] else "other"
        file_types[ext] = file_types.get(ext, 0) + 1

    # Determine project type
    project_type = "unknown"
    if languages.get("html", 0) > 0:
        project_type = "web (HTML/CSS/JS)"
    if languages.get("typescript", 0) > 0 or languages.get("javascript", 0) > 0:
        if (files_dir / "package.json").exists():
            project_type = "Node.js/React"
    if languages.get("python", 0) > 0:
        project_type = "Python" if "python" not in project_type else project_type

    # Build summary text
    summary_parts = [
        f"Project type: {project_type}",
        f"Total files: {len(index)}",
        f"Languages: {', '.join(f'{k}({v})' for k, v in sorted(languages.items(), key=lambda x: -x[1]))}",
        f"Key symbols: {', '.join(all_symbols[:15])}",
    ]

    # Add file list
    summary_parts.append("Files:")
    for entry in index[:20]:
        summary_parts.append(f"  - {entry['path']} ({entry.get('language', '?')}): {entry.get('summary', '')[:60]}")

    summary_text = "\n".join(summary_parts)

    # Store as memory
    remember(task_id, "project_summary", summary_text, metadata={
        "project_type": project_type,
        "file_count": len(index),
        "languages": languages,
    })

    # Store as artifact
    artifact_id = str(uuid.uuid4())[:12]
    db.create_artifact(
        artifact_id=artifact_id,
        task_id=task_id,
        artifact_type="report",
        name="project-summary.txt",
        path="project-summary",
        mime_type="text/plain",
        size=len(summary_text),
        metadata=f'{{"project_type": "{project_type}"}}',
    )

    return {
        "success": True,
        "task_id": task_id,
        "project_type": project_type,
        "file_count": len(index),
        "languages": languages,
        "symbols": all_symbols[:15],
        "summary": summary_text,
        "artifact_id": artifact_id,
    }
