"""Template Generator - creates project files from templates."""
import re
import uuid
import html
from pathlib import Path

from app.templates.registry import get_template
from app.workspace.manager import get_files_dir, resolve_safe_path
from app import database as db


def validate_template_variables(template_id: str, variables: dict) -> tuple[bool, list[str]]:
    """Validate variables for a template.

    Returns:
        Tuple of (is_valid, errors).
    """
    template = get_template(template_id)
    if not template:
        return False, [f"Template not found: {template_id}"]

    errors = []
    for var in template["variables"]:
        if var not in variables or not variables[var]:
            # Use defaults for optional vars
            if var == "primary_color":
                variables[var] = "#6366f1"
            elif var == "description":
                variables[var] = ""
            else:
                errors.append(f"Missing required variable: {var}")

    # Security: check for script injection in variables
    for key, value in variables.items():
        if isinstance(value, str):
            if "<script" in value.lower() or "javascript:" in value.lower():
                errors.append(f"Variable '{key}' contains potentially dangerous content")
            # Sanitize HTML in variables used in HTML context
            variables[key] = _sanitize_variable(value)

    return len(errors) == 0, errors


def generate_from_template(task_id: str, template_id: str, variables: dict) -> dict:
    """Generate project files from a template.

    Args:
        task_id: Task identifier.
        template_id: Template to use.
        variables: Template variables.

    Returns:
        Dict with success, generated files, artifacts.
    """
    template = get_template(template_id)
    if not template:
        return {"success": False, "error": f"Template not found: {template_id}"}

    # Validate
    valid, errors = validate_template_variables(template_id, variables)
    if not valid:
        return {"success": False, "errors": errors}

    files_dir = get_files_dir(task_id)
    files_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    artifacts = []

    for file_path, content_template in template["files"].items():
        # Security: validate path
        safe, resolved, reason = resolve_safe_path(task_id, file_path, "files")
        if not safe:
            from app.security.audit_log import log_security_event
            log_security_event(task_id, "file_access", "high", "template_write", file_path, "deny", reason)
            continue

        # Apply variables
        content = _apply_variables(content_template, variables)

        # Write file
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")

        # Register artifact
        artifact_id = str(uuid.uuid4())[:12]
        ext = Path(file_path).suffix
        mime = _guess_mime(ext)
        db.create_artifact(
            artifact_id=artifact_id,
            task_id=task_id,
            artifact_type="file",
            name=Path(file_path).name,
            path=file_path,
            mime_type=mime,
            size=len(content),
        )

        generated.append({"path": file_path, "size": len(content)})
        artifacts.append(artifact_id)

    return {
        "success": True,
        "template_id": template_id,
        "template_name": template["name"],
        "task_id": task_id,
        "files_generated": generated,
        "total_files": len(generated),
        "artifacts": artifacts,
    }


def _apply_variables(template: str, variables: dict) -> str:
    """Replace {{variable}} placeholders in template."""
    result = template
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result


def _sanitize_variable(value: str) -> str:
    """Sanitize a variable value for safe use in templates."""
    # Remove script tags and event handlers
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)
    value = value.replace("javascript:", "")
    return value


def _guess_mime(ext: str) -> str:
    mimes = {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
             ".jsx": "application/javascript", ".tsx": "text/typescript", ".json": "application/json",
             ".py": "text/x-python", ".md": "text/markdown", ".txt": "text/plain"}
    return mimes.get(ext, "application/octet-stream")
