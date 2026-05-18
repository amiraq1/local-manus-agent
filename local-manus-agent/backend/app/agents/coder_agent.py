"""Coder Agent - executes file creation and modification steps."""
import inspect

from app.agents.base_agent import BaseAgent, TaskContext
from app.security.permissions import Decision, check_command


class CoderAgent(BaseAgent):
    name = "CoderAgent"
    role = "Executes file creation, modification, and shell commands"

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Execute the plan steps (file operations and commands)."""
        self.log_step(ctx, "coding", "running")

        from app.agent.executor import execute_step
        from app.workspace.manager import set_current_task_id
        from app.tools.diff_tools import set_diff_task_id
        from app.tools.browser_tools import set_browser_task_id

        # Set workspace context
        set_current_task_id(ctx.task_id)
        set_diff_task_id(ctx.task_id)
        set_browser_task_id(ctx.task_id)

        executed = 0
        failed = 0

        for i, step in enumerate(ctx.plan):
            # Skip blocked steps
            if step.get("_blocked"):
                ctx.tool_results.append({
                    "success": False,
                    "error": f"Blocked by SecurityAgent: {step.get('_block_reason', '')}",
                    "tool": step.get("tool", ""),
                    "description": step.get("description", ""),
                })
                failed += 1
                continue

            # Skip browser/preview steps (handled by BrowserAgent)
            if step.get("tool", "").startswith("browser_") or step.get("tool") in ("start_preview", "stop_preview"):
                continue

            if step.get("tool") == "run_command":
                command = step.get("params", {}).get("command", "")
                decision, reason = check_command(ctx.task_id, command)
                if decision == Decision.DENY:
                    self._record_rejected(ctx, step, f"Blocked by policy: {reason}")
                    failed += 1
                    continue

                needs_approval = ctx.mode == "safe" or decision == Decision.REQUIRE_APPROVAL
                if needs_approval:
                    approved = await self._request_command_approval(ctx, command)
                    if not approved:
                        self._record_rejected(ctx, step, "Command rejected by user")
                        failed += 1
                        continue
                    step.setdefault("params", {})["approved"] = True

            result = await execute_step(step)
            ctx.tool_results.append(result)

            if result.get("success"):
                executed += 1
                # Track artifacts
                if result.get("result", {}).get("artifact_id") if isinstance(result.get("result"), dict) else False:
                    ctx.artifacts.append(result["result"]["artifact_id"])
            else:
                failed += 1
                ctx.errors.append(f"Step {i+1} failed: {result.get('error', '')}")

        summary = f"Executed {executed} steps"
        if failed:
            summary += f", {failed} failed"

        self.log_step(ctx, "coding", "completed", summary)
        return ctx

    async def _request_command_approval(self, ctx: TaskContext, command: str) -> bool:
        if not ctx.request_approval:
            return False
        result = ctx.request_approval(command)
        if inspect.isawaitable(result):
            result = await result
        return bool(result)

    def _record_rejected(self, ctx: TaskContext, step: dict, reason: str):
        ctx.tool_results.append({
            "success": False,
            "error": reason,
            "tool": step.get("tool", ""),
            "description": step.get("description", ""),
        })
        ctx.errors.append(f"{step.get('description', 'Step')} failed: {reason}")
