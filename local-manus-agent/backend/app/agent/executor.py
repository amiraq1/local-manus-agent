"""Executor module - runs individual steps from the plan."""
import asyncio
import inspect
from typing import Any

from app.tools.file_tools import read_file, write_file, edit_file, list_files, create_folder
from app.tools.shell_tools import run_command
from app.tools.preview_tools import start_preview, stop_preview, get_preview_url
from app.tools.diff_tools import get_file_diff, list_pending_changes, accept_file_change, reject_file_change
from app.tools.code_review_tools import review_code, run_project_checks, detect_runtime_errors, suggest_fixes, auto_fix
from app.tools.browser_tools import (
    browser_open_url,
    browser_get_text,
    browser_get_title,
    browser_click,
    browser_type,
    browser_screenshot,
    browser_evaluate,
    browser_close,
)


# Tool registry - includes both sync and async tools
TOOLS = {
    # File tools (sync)
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "list_files": list_files,
    "create_folder": create_folder,
    # Shell tools (sync)
    "run_command": run_command,
    # Preview tools (sync)
    "start_preview": start_preview,
    "stop_preview": stop_preview,
    "get_preview_url": get_preview_url,
    # Diff tools (sync)
    "get_file_diff": get_file_diff,
    "list_pending_changes": list_pending_changes,
    "accept_file_change": accept_file_change,
    "reject_file_change": reject_file_change,
    # Code review tools (sync - take task_id as first arg from workspace manager)
    "review_code": review_code,
    "run_project_checks": run_project_checks,
    "detect_runtime_errors": detect_runtime_errors,
    "suggest_fixes": suggest_fixes,
    "auto_fix": auto_fix,
    # Browser tools (async)
    "browser_open_url": browser_open_url,
    "browser_get_text": browser_get_text,
    "browser_get_title": browser_get_title,
    "browser_click": browser_click,
    "browser_type": browser_type,
    "browser_screenshot": browser_screenshot,
    "browser_evaluate": browser_evaluate,
    "browser_close": browser_close,
}


async def execute_step(step: dict) -> dict:
    """Execute a single step from the plan.

    Handles both sync and async tools transparently.

    Args:
        step: Dictionary with 'tool' and 'params' keys.

    Returns:
        Dictionary with execution result.
    """
    tool_name = step.get("tool", "")
    params = step.get("params", {})
    description = step.get("description", "Unknown step")

    if tool_name not in TOOLS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "description": description,
        }

    try:
        tool_fn = TOOLS[tool_name]

        # Call the tool - handle both sync and async
        if params:
            result = tool_fn(**params)
        else:
            result = tool_fn()

        # Await if it's a coroutine
        if inspect.isawaitable(result):
            result = await result

        # Normalize result
        if isinstance(result, dict):
            success = result.get("success", True)
            return {
                "success": success,
                "result": result,
                "tool": tool_name,
                "description": description,
            }
        else:
            return {
                "success": True,
                "result": result,
                "tool": tool_name,
                "description": description,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool": tool_name,
            "description": description,
        }
