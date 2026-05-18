"""Regression checks for command approval, sandbox fallback, and file diffs."""
import asyncio
import shutil
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import config
from app.agents.base_agent import TaskContext
from app.agents.coder_agent import CoderAgent
from app.tools.diff_tools import accept_file_change, set_diff_task_id
from app.tools.file_tools import write_file
from app.workspace.manager import get_files_dir, set_current_task_id


def _cleanup_task(task_id: str):
    shutil.rmtree(BACKEND_ROOT / "workspace" / "tasks" / task_id, ignore_errors=True)


def test_pending_file_changes_do_not_write():
    task_id = "security_regression_pending"
    _cleanup_task(task_id)
    old_mode = config.EXECUTION_MODE
    try:
        config.EXECUTION_MODE = "safe"
        set_current_task_id(task_id)
        set_diff_task_id(task_id)

        result = write_file("pending.txt", "hello")
        target = get_files_dir(task_id) / "pending.txt"

        assert result["success"] is True
        assert result["status"] == "pending"
        assert result["pending_approval"] is True
        assert not target.exists(), "Safe-mode pending changes must not be written before acceptance"

        accepted = accept_file_change(result["change_id"])
        assert accepted["success"] is True
        assert target.read_text(encoding="utf-8") == "hello"
    finally:
        config.EXECUTION_MODE = old_mode
        _cleanup_task(task_id)


def test_safe_mode_coder_requires_command_approval():
    async def run_check():
        ctx = TaskContext(task_id="security_regression_approval", user_message="probe", mode="safe")
        ctx.plan = [{
            "description": "probe command",
            "tool": "run_command",
            "params": {"command": "echo should_not_run"},
        }]
        return await CoderAgent().run(ctx)

    ctx = asyncio.run(run_check())
    assert ctx.tool_results
    assert ctx.tool_results[0]["success"] is False
    assert "rejected" in ctx.tool_results[0]["error"].lower()


def test_sandbox_enabled_does_not_fallback_to_host():
    import app.sandbox.docker_sandbox as docker_sandbox
    import app.tools.shell_tools as shell_tools

    class FakeSandbox:
        def _docker_available(self):
            return False

    old_enabled = shell_tools.SANDBOX_ENABLED
    old_get_sandbox = docker_sandbox.get_docker_sandbox
    try:
        shell_tools.SANDBOX_ENABLED = True
        docker_sandbox.get_docker_sandbox = lambda: FakeSandbox()
        result = shell_tools.run_command("echo should_not_run", approved=True)
        assert result["success"] is False
        assert result["sandbox"] is True
        assert "Docker sandbox is enabled" in result["error"]
    finally:
        shell_tools.SANDBOX_ENABLED = old_enabled
        docker_sandbox.get_docker_sandbox = old_get_sandbox


def test_approval_required_command_blocks_without_approval():
    import app.tools.shell_tools as shell_tools

    result = shell_tools.run_command("pip install sample-package")
    assert result["success"] is False
    assert result.get("requires_approval") is True


if __name__ == "__main__":
    test_pending_file_changes_do_not_write()
    print("PASS: test_pending_file_changes_do_not_write")
    test_safe_mode_coder_requires_command_approval()
    print("PASS: test_safe_mode_coder_requires_command_approval")
    test_sandbox_enabled_does_not_fallback_to_host()
    print("PASS: test_sandbox_enabled_does_not_fallback_to_host")
    test_approval_required_command_blocks_without_approval()
    print("PASS: test_approval_required_command_blocks_without_approval")
