"""Reviewer Agent - reviews code quality and runs project checks."""
import uuid
from app.agents.base_agent import BaseAgent, TaskContext


class ReviewerAgent(BaseAgent):
    name = "ReviewerAgent"
    role = "Reviews code quality, runs checks, and suggests fixes"

    async def run(self, ctx: TaskContext) -> TaskContext:
        """Run code review and project checks."""
        self.log_step(ctx, "review", "running")

        from app.tools.code_review_tools import run_project_checks, auto_fix
        from app.workspace.manager import get_files_dir
        from app import database as db

        # Run project checks
        checks = run_project_checks(ctx.task_id)
        total_errors = checks.get("total_errors", 0)
        total_warnings = checks.get("total_warnings", 0)

        # Auto-fix simple issues if in autonomous mode
        fixes_applied = 0
        if total_errors > 0 or total_warnings > 0:
            files_dir = get_files_dir(ctx.task_id)
            if files_dir.exists():
                for f in files_dir.rglob("*"):
                    if f.is_file() and f.suffix in (".html", ".js", ".jsx"):
                        rel = str(f.relative_to(files_dir)).replace("\\", "/")
                        if ctx.mode == "autonomous":
                            result = auto_fix(ctx.task_id, rel)
                            if result.get("changed"):
                                fixes_applied += result.get("total_fixes", 0)

        # Store review report as artifact
        report = f"Project checks: {checks.get('project_type', 'unknown')}\n"
        report += f"Errors: {total_errors}, Warnings: {total_warnings}\n"
        report += f"Auto-fixes applied: {fixes_applied}\n"
        if checks.get("checks"):
            for c in checks["checks"]:
                report += f"  [{c.get('check', '')}] errors={len(c.get('errors', []))}, warnings={len(c.get('warnings', []))}\n"

        artifact_id = str(uuid.uuid4())[:12]
        db.create_artifact(
            artifact_id=artifact_id,
            task_id=ctx.task_id,
            artifact_type="report",
            name="code-review-report.txt",
            path="code-review-report",
            mime_type="text/plain",
            size=len(report),
        )
        ctx.artifacts.append(artifact_id)

        summary = f"Errors: {total_errors}, Warnings: {total_warnings}, Fixes: {fixes_applied}"
        self.log_step(ctx, "review", "completed", summary)

        return ctx
