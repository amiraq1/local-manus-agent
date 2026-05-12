"""Planner Agent - creates execution plans from user tasks."""
from app.agents.base_agent import BaseAgent, TaskContext


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    role = "Decomposes user tasks into executable step-by-step plans"

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Create an execution plan."""
        self.log_step(ctx, "planning", "running")

        try:
            from app.agent.planner import create_plan
            result = await create_plan(ctx.user_message)

            if result.get("success"):
                ctx.plan = result["steps"]
                self.log_step(ctx, "planning", "completed",
                             f"Plan created with {len(ctx.plan)} steps")
            else:
                error = result.get("error", "Failed to create plan")
                ctx.errors.append(f"PlannerAgent: {error}")
                self.log_step(ctx, "planning", "error", error)

        except Exception as e:
            ctx.errors.append(f"PlannerAgent: {e}")
            self.log_step(ctx, "planning", "error", str(e))

        return ctx
