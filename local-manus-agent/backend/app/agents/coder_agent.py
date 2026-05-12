"""Coder Agent - executes file creation and modification steps."""
from app.agents.base_agent import BaseAgent, TaskContext


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
