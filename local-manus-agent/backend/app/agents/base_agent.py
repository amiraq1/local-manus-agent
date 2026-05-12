"""Base Agent class - foundation for all specialized agents."""
import time
import uuid
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class TaskContext:
    """Shared context passed between agents during task execution."""
    task_id: str
    user_message: str
    mode: str = "safe"
    workspace_paths: dict = field(default_factory=dict)
    retrieved_context: list = field(default_factory=list)
    plan: list = field(default_factory=list)
    tool_results: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    final_summary: str = ""
    agent_steps: list = field(default_factory=list)


class BaseAgent:
    """Abstract base for all specialized agents."""

    name: str = "BaseAgent"
    role: str = "Generic agent"
    system_prompt: str = ""

    def __init__(self):
        self._events: list[dict] = []

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Execute this agent's logic on the task context.

        Args:
            ctx: Shared TaskContext.

        Returns:
            Updated TaskContext.
        """
        raise NotImplementedError

    def log_step(self, ctx: TaskContext, phase: str, status: str, summary: str = ""):
        """Record an agent step."""
        step = {
            "id": str(uuid.uuid4())[:12],
            "task_id": ctx.task_id,
            "agent_name": self.name,
            "phase": phase,
            "status": status,
            "summary": summary,
            "created_at": time.time(),
        }
        ctx.agent_steps.append(step)
        self._events.append(step)
        return step

    def emit_event(self, ctx: TaskContext, phase: str, status: str, summary: str = "") -> dict:
        """Create a WebSocket-compatible event dict."""
        return {
            "type": "agent_step",
            "task_id": ctx.task_id,
            "agent": self.name,
            "phase": phase,
            "status": status,
            "summary": summary,
        }

    def get_events(self) -> list[dict]:
        """Get and clear pending events."""
        events = self._events[:]
        self._events.clear()
        return events
