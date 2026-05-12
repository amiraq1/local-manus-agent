"""Memory Agent - retrieves context and stores memories."""
from app.agents.base_agent import BaseAgent, TaskContext


class MemoryAgent(BaseAgent):
    name = "MemoryAgent"
    role = "Retrieves relevant context from project files and past memories"

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Retrieve relevant context for the task."""
        self.log_step(ctx, "retrieval", "running")

        try:
            from app.memory.retriever import get_relevant_context
            from app.memory.indexer import index_task_files

            # Index files first (incremental - skips unchanged)
            index_task_files(ctx.task_id)

            # Retrieve context
            result = get_relevant_context(ctx.task_id, ctx.user_message, limit=5)
            if result.get("success"):
                ctx.retrieved_context = result.get("context", [])

            self.log_step(ctx, "retrieval", "completed",
                         f"Retrieved {len(ctx.retrieved_context)} context items")
        except Exception as e:
            self.log_step(ctx, "retrieval", "error", str(e))
            ctx.errors.append(f"MemoryAgent: {e}")

        return ctx

    async def store_post_task(self, ctx: TaskContext):
        """Store memories after task completion."""
        try:
            from app.memory.memory_store import remember

            if ctx.final_summary:
                remember(ctx.task_id, "project_summary", ctx.final_summary)

            if ctx.errors:
                for err in ctx.errors[:3]:
                    remember(ctx.task_id, "error", err)

        except Exception:
            pass
