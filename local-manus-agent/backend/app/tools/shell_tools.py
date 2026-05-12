"""Shell command tools for the agent.

Supports two execution modes:
- Local: runs commands directly on the host (when SANDBOX_ENABLED=False)
- Sandbox: runs commands inside a Docker container (when SANDBOX_ENABLED=True)
"""
import subprocess
import os

from config import SANDBOX_ENABLED
from app.tools.safety import is_command_safe
from app.workspace.manager import get_current_task_id, get_files_dir


def run_command(command: str) -> dict:
    """Run a shell command, using sandbox if enabled.

    The command is first validated by the safety module.
    Then it's executed either locally or in a Docker sandbox.

    Args:
        command: Shell command to execute.

    Returns:
        Dict with success status, stdout, stderr, and return code.
    """
    # Safety check (applies regardless of sandbox mode)
    safe, reason = is_command_safe(command)
    if not safe:
        return {
            "success": False,
            "error": f"Command blocked: {reason}",
            "command": command,
            "sandbox": SANDBOX_ENABLED,
        }

    if SANDBOX_ENABLED:
        return _run_in_sandbox(command)
    else:
        return _run_locally(command)


def _run_in_sandbox(command: str) -> dict:
    """Run command inside Docker sandbox."""
    from app.sandbox.docker_sandbox import get_docker_sandbox
    from app.tools.diff_tools import get_diff_task_id

    sandbox = get_docker_sandbox()
    task_id = get_diff_task_id()  # reuse the current task context

    result = sandbox.run_command(task_id, command)

    return {
        "success": result.success,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "command": command,
        "sandbox": True,
        "timed_out": result.timed_out,
        "error": result.error,
    }


def _run_locally(command: str) -> dict:
    """Run command directly on the host in the current task's files dir."""
    task_id = get_current_task_id()
    cwd = str(get_files_dir(task_id))

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "HOME": cwd},
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
            "command": command,
            "sandbox": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out (60s limit)",
            "command": command,
            "sandbox": False,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command,
            "sandbox": False,
        }
