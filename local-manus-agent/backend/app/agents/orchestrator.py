"""Orchestrator - coordinates all agents in sequence."""
import asyncio
from typing import AsyncGenerator

from app.agents.base_agent import TaskContext
from app.agents.memory_agent import MemoryAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.security_agent import SecurityAgent
from app.agents.coder_agent import CoderAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.browser_agent import BrowserAgent
from app.workspace.manager import set_current_task_id, get_files_dir
from app import database as db


class Orchestrator:
    """Coordinates specialized agents in the execution pipeline.

    Flow: Memory → Planner → Security → Coder → Reviewer → Browser → Reviewer → Summary
    """

    def __init__(self):
        self.memory_agent = MemoryAgent()
        self.planner_agent = PlannerAgent()
        self.security_agent = SecurityAgent()
        self.coder_agent = CoderAgent()
        self.reviewer_agent = ReviewerAgent()
        self.browser_agent = BrowserAgent()

    async def run(self, task_id: str, user_message: str, mode: str = "safe") -> AsyncGenerator[dict, None]:
        """Run the full agent pipeline, yielding events for streaming.

        Args:
            task_id: Task identifier.
            user_message: User's task description.
            mode: Execution mode (safe/autonomous).

        Yields:
            Event dicts for WebSocket streaming.
        """
        # Initialize context
        set_current_task_id(task_id)
        files_dir = get_files_dir(task_id)

        ctx = TaskContext(
            task_id=task_id,
            user_message=user_message,
            mode=mode,
            workspace_paths={"files": str(files_dir)},
        )

        # --- Phase 1: Memory Agent ---
        yield self._event(ctx, "MemoryAgent", "retrieval", "running")
        ctx = await self.memory_agent.run(ctx)
        yield self._event(ctx, "MemoryAgent", "retrieval", "completed",
                         f"Retrieved {len(ctx.retrieved_context)} context items")

        # --- Phase 2: Planner Agent ---
        yield self._event(ctx, "PlannerAgent", "planning", "running")
        ctx = await self.planner_agent.run(ctx)
        if ctx.plan:
            yield self._event(ctx, "PlannerAgent", "planning", "completed",
                             f"Plan: {len(ctx.plan)} steps")
            yield {"type": "plan_ready", "task_id": task_id, "plan": ctx.plan}
        else:
            yield self._event(ctx, "PlannerAgent", "planning", "error",
                             "Failed to create plan")
            ctx.final_summary = "Failed to create execution plan."
            yield {"type": "task_summary", "task_id": task_id, "summary": ctx.final_summary}
            return

        # --- Phase 3: Security Agent ---
        yield self._event(ctx, "SecurityAgent", "security_review", "running")
        ctx = await self.security_agent.run(ctx)
        blocked = sum(1 for s in ctx.plan if s.get("_blocked"))
        yield self._event(ctx, "SecurityAgent", "security_review", "completed",
                         f"Blocked {blocked} dangerous steps" if blocked else "All steps approved")

        # --- Phase 4: Coder Agent ---
        yield self._event(ctx, "CoderAgent", "coding", "running")
        ctx = await self.coder_agent.run(ctx)
        successes = sum(1 for r in ctx.tool_results if r.get("success"))
        yield self._event(ctx, "CoderAgent", "coding", "completed",
                         f"{successes}/{len(ctx.tool_results)} steps succeeded")

        # --- Phase 5: Reviewer Agent ---
        yield self._event(ctx, "ReviewerAgent", "review", "running")
        ctx = await self.reviewer_agent.run(ctx)
        yield self._event(ctx, "ReviewerAgent", "review", "completed",
                         ctx.agent_steps[-1]["summary"] if ctx.agent_steps else "")

        # --- Phase 6: Browser Agent ---
        yield self._event(ctx, "BrowserAgent", "browser", "running")
        ctx = await self.browser_agent.run(ctx)
        yield self._event(ctx, "BrowserAgent", "browser", "completed",
                         ctx.agent_steps[-1]["summary"] if ctx.agent_steps else "")

        # --- Phase 7: Final Summary ---
        ctx.final_summary = self._build_summary(ctx)
        yield self._event(ctx, "Orchestrator", "summary", "completed", ctx.final_summary)

        # Store memories post-task
        await self.memory_agent.store_post_task(ctx)

        # Save agent steps to DB
        self._save_steps(ctx)

        yield {"type": "task_summary", "task_id": task_id, "summary": ctx.final_summary,
               "artifacts": ctx.artifacts, "errors": ctx.errors}

    def _event(self, ctx: TaskContext, agent: str, phase: str, status: str, summary: str = "") -> dict:
        """Create a WebSocket event."""
        return {
            "type": "agent_step",
            "task_id": ctx.task_id,
            "agent": agent,
            "phase": phase,
            "status": status,
            "summary": summary,
        }

    def _build_summary(self, ctx: TaskContext) -> str:
        """Build final task summary."""
        parts = []
        successes = sum(1 for r in ctx.tool_results if r.get("success"))
        total = len(ctx.tool_results)

        if successes == total and total > 0:
            parts.append(f"Task completed successfully ({successes} steps).")
        elif total > 0:
            parts.append(f"Task partially completed ({successes}/{total} steps succeeded).")
        else:
            parts.append("No steps were executed.")

        if ctx.artifacts:
            parts.append(f"Created {len(ctx.artifacts)} artifacts.")

        if ctx.errors:
            parts.append(f"Encountered {len(ctx.errors)} issues.")

        return " ".join(parts)

    def _save_steps(self, ctx: TaskContext):
        """Save agent steps to database."""
        from app.database import get_db
        with get_db() as conn:
            for step in ctx.agent_steps:
                conn.execute("""
                    INSERT OR IGNORE INTO agent_steps (id, task_id, agent_name, phase, input_summary, output_summary, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    step["id"], step["task_id"], step["agent_name"],
                    step["phase"], "", step.get("summary", ""),
                    step["status"], step["created_at"],
                ))
