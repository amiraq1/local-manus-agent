"""Browser Agent - handles preview, screenshots, and visual verification."""
from app.agents.base_agent import BaseAgent, TaskContext


class BrowserAgent(BaseAgent):
    name = "BrowserAgent"
    role = "Starts preview, opens pages, takes screenshots, verifies output"

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Run preview and browser verification if plan includes browser steps."""
        # Check if plan has any preview/browser steps
        has_preview = any(s.get("tool") in ("start_preview", "browser_open_url", "browser_screenshot")
                         for s in ctx.plan)
        if not has_preview:
            self.log_step(ctx, "browser", "skipped", "No browser steps in plan")
            return ctx

        self.log_step(ctx, "browser", "running")

        from app.agent.executor import execute_step
        from app.workspace.manager import set_current_task_id
        from app.tools.browser_tools import set_browser_task_id

        set_current_task_id(ctx.task_id)
        set_browser_task_id(ctx.task_id)

        executed = 0
        for step in ctx.plan:
            tool = step.get("tool", "")
            if tool in ("start_preview", "stop_preview") or tool.startswith("browser_"):
                result = await execute_step(step)
                ctx.tool_results.append(result)
                if result.get("success"):
                    executed += 1
                    # Track screenshot artifacts
                    res = result.get("result", {})
                    if isinstance(res, dict) and res.get("artifact_id"):
                        ctx.artifacts.append(res["artifact_id"])

        self.log_step(ctx, "browser", "completed", f"Executed {executed} browser steps")
        return ctx
