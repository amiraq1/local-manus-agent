"""Main Agent - orchestrates Plan → Act → Observe → Review → Fix → Final cycle."""
import asyncio
from typing import AsyncGenerator, Callable, Optional

from app.agent.planner import create_plan
from app.agent.executor import execute_step
from app.agent.reviewer import review_execution
from app.tools.browser_tools import set_browser_task_id
from app.tools.diff_tools import set_diff_task_id
from app.workspace.manager import set_current_task_id
from app import database as db
from config import MAX_STEPS, MAX_RETRIES


class Agent:
    """Local Manus Agent that processes tasks through a structured pipeline.

    Supports two modes:
    - safe: requires user approval for shell commands
    - autonomous: executes all commands without approval
    """

    def __init__(self, task_id: str, mode: str = "safe"):
        self.task_id = task_id
        self.mode = mode
        self.task: str = ""
        self.plan: list[dict] = []
        self.results: list[dict] = []
        self.tool_log: list[dict] = []
        self.request_approval: Optional[Callable] = None

    async def run(self, task: str) -> AsyncGenerator[dict, None]:
        """Run the agent on a task, yielding events for real-time streaming.

        Follows: Plan → Act → Observe → Review → Fix → Final

        Args:
            task: User's task description.

        Yields:
            Event dictionaries for each phase of execution.
        """
        self.task = task
        self.results = []
        self.tool_log = []

        # Set browser task context
        set_browser_task_id(self.task_id)
        set_diff_task_id(self.task_id)
        set_current_task_id(self.task_id)

        # Phase 1: Thinking
        yield {"phase": "thinking", "content": f"Analyzing task: {task}"}
        db.add_message(self.task_id, "agent", f"Analyzing task: {task}", "thinking")
        await asyncio.sleep(0.3)

        # Phase 2: Planning
        yield {"phase": "planning", "content": "Creating execution plan..."}
        db.add_message(self.task_id, "agent", "Creating execution plan...", "planning")

        plan_result = await create_plan(task)

        if not plan_result.get("success"):
            error_msg = f"Failed to create plan: {plan_result.get('error', 'Unknown error')}"
            yield {"phase": "error", "content": error_msg}
            db.add_message(self.task_id, "agent", error_msg, "error")
            db.update_task_status(self.task_id, "failed", error_msg)
            return

        self.plan = plan_result["steps"]
        db.save_plan_steps(self.task_id, self.plan)

        yield {
            "phase": "plan_ready",
            "content": f"Plan created with {len(self.plan)} steps",
            "plan": self.plan,
        }
        db.add_message(self.task_id, "agent", f"Plan created with {len(self.plan)} steps", "plan_ready")

        # Phase 3: Execution (Act + Observe)
        step_index = 0

        while step_index < len(self.plan) and step_index < MAX_STEPS:
            step = self.plan[step_index]

            yield {
                "phase": "executing",
                "content": f"Step {step_index + 1}: {step.get('description', '')}",
                "step_index": step_index,
                "tool": step.get("tool", ""),
            }
            db.update_step_status(self.task_id, step_index, "running")

            # Check if this is a shell command that needs approval
            if step.get("tool") == "run_command" and self.mode == "safe":
                command = step.get("params", {}).get("command", "")
                approved = await self._request_command_approval(command)

                if not approved:
                    result = {
                        "success": False,
                        "error": "Command rejected by user",
                        "tool": "run_command",
                        "description": step.get("description", ""),
                    }
                    self.results.append(result)
                    db.update_step_status(self.task_id, step_index, "rejected", "User rejected command")
                    db.add_tool_log(self.task_id, step_index, "run_command", step.get("params", {}), False, "Rejected")

                    yield {
                        "phase": "observation",
                        "content": f"Step {step_index + 1} rejected by user",
                        "result": result,
                        "tool_log": {"step": step_index + 1, "tool": "run_command", "params": step.get("params", {}), "success": False},
                    }
                    step_index += 1
                    continue

            # Execute the step
            result = await execute_step(step)
            self.results.append(result)

            # Determine status
            step_status = "done" if result.get("success") else "error"
            db.update_step_status(self.task_id, step_index, step_status, str(result.get("error", "")))

            # Log tool usage
            log_entry = {
                "step": step_index + 1,
                "tool": step.get("tool", ""),
                "params": step.get("params", {}),
                "success": result.get("success", False),
            }
            self.tool_log.append(log_entry)
            db.add_tool_log(
                self.task_id, step_index, step.get("tool", ""),
                step.get("params", {}), result.get("success", False),
                str(result.get("result", ""))[:500],
            )

            # Track created files
            if result.get("success") and step.get("tool") == "write_file":
                path = step.get("params", {}).get("path", "")
                size = result.get("result", {}).get("size", 0) if isinstance(result.get("result"), dict) else 0
                db.add_created_file(self.task_id, path, size)

            yield {
                "phase": "observation",
                "content": f"Step {step_index + 1} {'completed' if result['success'] else 'failed'}",
                "result": result,
                "tool_log": log_entry,
            }
            db.add_message(
                self.task_id, "agent",
                f"Step {step_index + 1} {'completed' if result['success'] else 'failed'}: {step.get('description', '')}",
                "observation",
            )

            step_index += 1

        # Phase 4: Review
        yield {"phase": "reviewing", "content": "Reviewing execution results..."}
        db.add_message(self.task_id, "agent", "Reviewing execution results...", "reviewing")

        review = await review_execution(task, self.results)

        # Phase 5: Fix (if needed)
        if review.get("status") == "needs_fix":
            fixes = review.get("fixes", [])
            retry_count = 0

            while fixes and retry_count < MAX_RETRIES:
                retry_count += 1
                yield {
                    "phase": "fixing",
                    "content": f"Applying fixes (attempt {retry_count}/{MAX_RETRIES})",
                    "fixes": fixes,
                }
                db.add_message(self.task_id, "agent", f"Applying fixes (attempt {retry_count}/{MAX_RETRIES})", "fixing")

                for fix in fixes:
                    # Check approval for fix commands too
                    if fix.get("tool") == "run_command" and self.mode == "safe":
                        command = fix.get("params", {}).get("command", "")
                        approved = await self._request_command_approval(command)
                        if not approved:
                            continue

                    fix_result = await execute_step(fix)
                    self.results.append(fix_result)
                    db.add_tool_log(
                        self.task_id, -1, fix.get("tool", ""),
                        fix.get("params", {}), fix_result.get("success", False),
                        "fix",
                    )

                    yield {
                        "phase": "fix_applied",
                        "content": f"Fix: {fix.get('description', '')}",
                        "result": fix_result,
                    }

                # Re-review after fixes
                review = await review_execution(task, self.results)
                if review.get("status") != "needs_fix":
                    break
                fixes = review.get("fixes", [])

        # Phase 6: Final
        summary = review.get("summary", "Task completed successfully.")
        final_event = {
            "phase": "completed",
            "content": summary,
            "tool_log": self.tool_log,
            "total_steps": len(self.results),
        }
        yield final_event
        db.add_message(self.task_id, "agent", summary, "completed")

    async def _request_command_approval(self, command: str) -> bool:
        """Request user approval for a shell command.

        Args:
            command: The command to approve.

        Returns:
            True if approved, False if rejected.
        """
        if self.request_approval:
            return await self.request_approval(command)
        # If no approval callback, default to rejecting in safe mode
        return self.mode == "autonomous"
