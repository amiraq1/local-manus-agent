"""Goal Runner - executes a goal end-to-end."""
import uuid
import asyncio
from typing import AsyncGenerator

from app.goals.goal_analyzer import analyze_goal
from app.goals.models import GoalAnalysis, GoalStatus
from app.templates.generator import generate_from_template
from app.tools.code_review_tools import run_project_checks
from app.tools.preview_tools import start_preview, get_preview_url
from app.artifacts.exporter import create_task_export
from app.workspace.manager import set_current_task_id, create_task_workspace
from app.tools.diff_tools import set_diff_task_id
from app import database as db


async def run_goal(message: str, mode: str = "safe") -> AsyncGenerator[dict, None]:
    """Run a goal end-to-end, yielding events for streaming.

    Steps:
    1. Create task
    2. Analyze goal
    3. Select and generate template
    4. Run code review
    5. Start preview (if web)
    6. Create export ZIP
    7. Return summary

    Args:
        message: User's goal description.
        mode: Execution mode.

    Yields:
        Event dicts for WebSocket streaming.
    """
    task_id = str(uuid.uuid4())[:12]

    # 1. Create task
    db.create_task(task_id, message, mode)
    db.add_message(task_id, "user", message)
    set_current_task_id(task_id)
    set_diff_task_id(task_id)
    create_task_workspace(task_id)

    yield {"type": "goal_started", "task_id": task_id, "message": message}

    # 2. Analyze goal
    yield {"type": "goal_phase", "task_id": task_id, "phase": "analyzing", "progress": 10}

    analysis = analyze_goal(message)

    yield {
        "type": "goal_analyzed",
        "task_id": task_id,
        "project_type": analysis.project_type,
        "template": analysis.recommended_template,
        "variables": analysis.variables,
        "confidence": analysis.confidence,
        "reasoning": analysis.reasoning,
        "progress": 20,
    }

    db.add_message(task_id, "agent", f"Analyzed: {analysis.reasoning}", "planning")

    # 3. Generate template
    yield {"type": "goal_phase", "task_id": task_id, "phase": "generating", "progress": 30}
    yield {"type": "template_selected", "task_id": task_id, "template_id": analysis.recommended_template}

    gen_result = generate_from_template(task_id, analysis.recommended_template, analysis.variables)

    if not gen_result.get("success"):
        yield {"type": "goal_failed", "task_id": task_id, "error": gen_result.get("error", "Generation failed")}
        db.update_task_status(task_id, "failed", gen_result.get("error", ""))
        return

    yield {
        "type": "template_generated",
        "task_id": task_id,
        "files": gen_result.get("files_generated", []),
        "total_files": gen_result.get("total_files", 0),
        "progress": 50,
    }

    db.add_message(task_id, "agent", f"Generated {gen_result['total_files']} files from {analysis.recommended_template}", "executing")

    # 4. Code review
    yield {"type": "goal_phase", "task_id": task_id, "phase": "reviewing", "progress": 60}

    checks = run_project_checks(task_id)

    yield {
        "type": "review_completed",
        "task_id": task_id,
        "errors": checks.get("total_errors", 0),
        "warnings": checks.get("total_warnings", 0),
        "progress": 70,
    }

    # 5. Preview (if web project)
    preview_url = None
    if analysis.project_type == "web":
        yield {"type": "goal_phase", "task_id": task_id, "phase": "previewing", "progress": 80}

        preview_result = start_preview()
        if preview_result.get("success"):
            preview_url = preview_result.get("url")
            yield {"type": "preview_started", "task_id": task_id, "url": preview_url, "progress": 85}

    # 6. Export ZIP
    yield {"type": "goal_phase", "task_id": task_id, "phase": "exporting", "progress": 90}

    export_result = create_task_export(task_id)
    export_info = None
    if export_result.get("success"):
        export_info = {"filename": export_result["filename"], "size": export_result["size"]}
        yield {"type": "export_created", "task_id": task_id, "export": export_info, "progress": 95}

    # 7. Complete
    summary = f"Created {analysis.recommended_template} project '{analysis.variables.get('project_name', '')}' with {gen_result['total_files']} files."
    if preview_url:
        summary += f" Preview: {preview_url}"

    db.update_task_status(task_id, "completed", summary)
    db.add_message(task_id, "agent", summary, "completed")

    yield {
        "type": "goal_completed",
        "task_id": task_id,
        "summary": summary,
        "template": analysis.recommended_template,
        "files_count": gen_result["total_files"],
        "preview_url": preview_url,
        "export": export_info,
        "progress": 100,
    }
