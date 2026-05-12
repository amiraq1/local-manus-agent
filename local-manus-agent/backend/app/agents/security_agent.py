"""Security Agent - reviews plans and commands for safety."""
from app.agents.base_agent import BaseAgent, TaskContext
from app.tools.safety import is_command_safe


class SecurityAgent(BaseAgent):
    name = "SecurityAgent"
    role = "Reviews execution plans and commands for security risks"

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Review the plan for security issues."""
        self.log_step(ctx, "security_review", "running")

        blocked = []
        approved = []

        for i, step in enumerate(ctx.plan):
            tool = step.get("tool", "")
            params = step.get("params", {})

            if tool == "run_command":
                command = params.get("command", "")
                safe, reason = is_command_safe(command)
                if not safe:
                    blocked.append({
                        "step": i,
                        "command": command,
                        "reason": reason,
                    })
                    step["_blocked"] = True
                    step["_block_reason"] = reason
                else:
                    approved.append(i)
            else:
                approved.append(i)

        summary = f"Approved {len(approved)} steps"
        if blocked:
            summary += f", blocked {len(blocked)} dangerous commands"
            for b in blocked:
                ctx.errors.append(f"SecurityAgent blocked step {b['step']}: {b['reason']}")

        self.log_step(ctx, "security_review", "completed", summary)
        return ctx

    def check_command(self, command: str) -> tuple[bool, str]:
        """Check a single command for safety."""
        return is_command_safe(command)
