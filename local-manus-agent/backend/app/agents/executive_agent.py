"""Executive Agent — Processes user input into structured JSON actions.

Wraps the LLM with the Executive persona to enforce:
- JSON-only responses (no markdown, no prose)
- Bento Box grid layouts for UI generation
- Dark + neon color scheme defaults
- Minimal key names for memory efficiency
"""
import json
import logging
from typing import Optional

from app.agents.base_agent import BaseAgent, TaskContext
from app.agents.executive_prompt import (
    EXECUTIVE_SYSTEM_PROMPT,
    EXECUTIVE_RESPONSE_SCHEMA,
    DESIGN_DEFAULTS,
    STATUS_SUCCESS,
    STATUS_ERROR,
    STATUS_CLARIFY,
    ACTION_RENDER,
    ACTION_EXECUTE,
    ACTION_STORE,
    ACTION_ANALYZE,
    ACTION_PLAN,
)

logger = logging.getLogger(__name__)


class ExecutiveAgent(BaseAgent):
    """Autonomous Executive Agent — converts input to actionable JSON."""

    name = "ExecutiveAgent"
    role = "Processes user input into structured actionable JSON payloads"
    system_prompt = EXECUTIVE_SYSTEM_PROMPT

    def __init__(self):
        super().__init__()
        self._design = DESIGN_DEFAULTS.copy()

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Execute via the orchestrator pipeline."""
        self.log_step(ctx, "executive_processing", "running")

        response = await self.process(ctx.user_message)
        ctx.final_summary = json.dumps(response, ensure_ascii=False)

        status = "completed" if response["status"] == STATUS_SUCCESS else "error"
        self.log_step(ctx, "executive_processing", status,
                      response.get("thought_process", ""))
        return ctx

    async def process(self, user_input: str) -> dict:
        """Process a user input string into structured JSON.

        Args:
            user_input: Raw user message.

        Returns:
            Validated JSON dict matching EXECUTIVE_RESPONSE_SCHEMA.
        """
        from app.llm.base import get_llm_provider

        llm = get_llm_provider()
        prompt = EXECUTIVE_SYSTEM_PROMPT.format(user_input=user_input)

        try:
            raw = await llm.generate(prompt)
            parsed = self._parse_response(raw)

            if parsed:
                # Inject design defaults for render_widget actions
                if parsed.get("action_type") == ACTION_RENDER:
                    parsed["payload"].setdefault("design", self._design)
                return parsed

            # LLM returned non-JSON — wrap as error
            return {
                "status": STATUS_ERROR,
                "action_type": ACTION_ANALYZE,
                "thought_process": "استجابة LLM غير صالحة كـ JSON، تم تغليفها",
                "payload": {"raw": raw[:500], "parse_error": True},
            }

        except Exception as e:
            logger.error(f"ExecutiveAgent.process failed: {e}")
            return {
                "status": STATUS_ERROR,
                "action_type": ACTION_ANALYZE,
                "thought_process": f"خطأ داخلي: {str(e)[:100]}",
                "payload": {"error": str(e)},
            }

    def _parse_response(self, raw: str) -> Optional[dict]:
        """Extract and validate JSON from LLM response.

        Handles cases where LLM wraps JSON in markdown fences or adds prose.

        Args:
            raw: Raw LLM output string.

        Returns:
            Parsed dict if valid, None otherwise.
        """
        text = raw.strip()

        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last fence lines
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            text = "\n".join(lines[start:end]).strip()

        # Find JSON object boundaries
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1

        if brace_start < 0 or brace_end <= brace_start:
            return None

        json_str = text[brace_start:brace_end]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return None

        # Validate required keys
        required = {"status", "action_type", "thought_process", "payload"}
        if not required.issubset(data.keys()):
            # Auto-fill missing keys
            data.setdefault("status", STATUS_SUCCESS)
            data.setdefault("action_type", ACTION_ANALYZE)
            data.setdefault("thought_process", "")
            data.setdefault("payload", {})

        # Validate status
        if data["status"] not in (STATUS_SUCCESS, STATUS_ERROR, STATUS_CLARIFY):
            data["status"] = STATUS_SUCCESS

        # Validate action_type
        valid_actions = {ACTION_RENDER, ACTION_EXECUTE, ACTION_STORE, ACTION_ANALYZE, ACTION_PLAN}
        if data["action_type"] not in valid_actions:
            data["action_type"] = ACTION_ANALYZE

        return data

    async def process_with_context(self, user_input: str, context: list[dict] = None) -> dict:
        """Process input with retrieved context (for RAG-enhanced responses).

        Args:
            user_input: Raw user message.
            context: Optional list of context items from memory/retrieval.

        Returns:
            Validated JSON dict.
        """
        if context:
            context_str = "\n".join(
                f"- {c.get('content', '')[:200]}" for c in context[:5]
            )
            enhanced_input = f"{user_input}\n\n## سياق مسترجع:\n{context_str}"
        else:
            enhanced_input = user_input

        return await self.process(enhanced_input)

    def create_widget_response(self, widget_type: str, props: dict,
                                children: list = None) -> dict:
        """Helper to create a render_widget response.

        Args:
            widget_type: UI component type (e.g., 'card', 'grid', 'chart').
            props: Component properties.
            children: Optional nested child widgets.

        Returns:
            Structured render_widget JSON.
        """
        payload = {
            "widget": widget_type,
            "props": props,
            "design": self._design,
        }
        if children:
            payload["children"] = children

        return {
            "status": STATUS_SUCCESS,
            "action_type": ACTION_RENDER,
            "thought_process": f"تصيير مكون {widget_type}",
            "payload": payload,
        }

    def create_command_response(self, steps: list[dict]) -> dict:
        """Helper to create an execute_command response.

        Args:
            steps: List of execution step dicts.

        Returns:
            Structured execute_command JSON.
        """
        return {
            "status": STATUS_SUCCESS,
            "action_type": ACTION_EXECUTE,
            "thought_process": f"تنفيذ {len(steps)} خطوات",
            "payload": {"steps": steps},
        }
