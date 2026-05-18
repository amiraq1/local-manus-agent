"""Security Agent - reviews plans and commands for safety."""
from app.agents.base_agent import BaseAgent, TaskContext
from app.security.permissions import Decision, check_command


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
                decision, reason = check_command(ctx.task_id, command)
                if decision == Decision.DENY:
                    blocked.append({
                        "step": i,
                        "command": command,
                        "reason": reason,
                    })
                    step["_blocked"] = True
                    step["_block_reason"] = reason
                else:
                    if decision == Decision.REQUIRE_APPROVAL:
                        step["_requires_approval"] = True
                        step["_approval_reason"] = reason
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
        decision, reason = check_command("", command)
        return decision != Decision.DENY, reason
