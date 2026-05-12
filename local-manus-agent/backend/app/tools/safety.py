"""Safety module - validates all operations before execution."""
import os
from pathlib import Path

from config import WORKSPACE_DIR, BLOCKED_COMMANDS, BLOCKED_PATH_PATTERNS


def is_path_safe(path: str) -> tuple[bool, str]:
    """Check if a file path is safe (within workspace).

    Args:
        path: The path to validate.

    Returns:
        Tuple of (is_safe, reason).
    """
    try:
        # Resolve the full path
        if os.path.isabs(path):
            resolved = Path(path).resolve()
        else:
            resolved = (WORKSPACE_DIR / path).resolve()

        # Check if path is within workspace
        workspace_resolved = WORKSPACE_DIR.resolve()
        if not str(resolved).startswith(str(workspace_resolved)):
            return False, f"Path escapes workspace: {path}"

        # Check blocked patterns
        path_str = str(resolved).replace("\\", "/")
        for pattern in BLOCKED_PATH_PATTERNS:
            if pattern in path_str:
                return False, f"Path matches blocked pattern: {pattern}"

        return True, "OK"
    except Exception as e:
        return False, f"Path validation error: {str(e)}"


def is_command_safe(command: str) -> tuple[bool, str]:
    """Check if a shell command is safe to execute.

    Args:
        command: The command string to validate.

    Returns:
        Tuple of (is_safe, reason).
    """
    cmd_lower = command.lower().strip()

    # Check against blocked commands
    for blocked in BLOCKED_COMMANDS:
        if blocked.lower() in cmd_lower:
            return False, f"Command contains blocked pattern: {blocked}"

    # Check for path traversal attempts
    if ".." in command and ("/" in command or "\\" in command):
        # Allow relative paths within workspace but flag suspicious ones
        parts = command.split()
        for part in parts:
            if "../../../" in part:
                return False, "Excessive path traversal detected"

    # Check for pipe to shell patterns
    dangerous_pipes = ["| bash", "| sh", "| zsh", "| cmd", "| powershell"]
    for pipe in dangerous_pipes:
        if pipe in cmd_lower:
            return False, f"Dangerous pipe pattern: {pipe}"

    return True, "OK"


def sanitize_path(path: str) -> Path:
    """Sanitize and resolve a path relative to workspace.

    Args:
        path: Input path (relative or absolute).

    Returns:
        Resolved Path object within workspace.

    Raises:
        ValueError: If path is not safe.
    """
    safe, reason = is_path_safe(path)
    if not safe:
        raise ValueError(reason)

    if os.path.isabs(path):
        return Path(path).resolve()
    return (WORKSPACE_DIR / path).resolve()
