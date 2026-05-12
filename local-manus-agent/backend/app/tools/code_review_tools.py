"""Code Review Tools - reviews code quality, detects errors, suggests fixes.

All functions accept task_id to operate within the correct task workspace.
"""
import subprocess
import re
import uuid
import json
from pathlib import Path
from typing import Optional

from app.workspace.manager import resolve_safe_path, get_files_dir, get_current_task_id
from app import database as db

# Common issues patterns by file type
HTML_ISSUES = [
    (r"<img[^>]*(?<!/)>(?!.*alt=)", "img tag missing alt attribute"),
    (r"<html[^>]*(?!.*lang=)", "html tag missing lang attribute"),
]

CSS_ISSUES = [
    (r"!important", "Avoid !important - use specificity instead"),
]

JS_ISSUES = [
    (r"\bvar\b", "Use 'let' or 'const' instead of 'var'"),
    (r"==(?!=)", "Use === instead of == for strict equality"),
    (r"console\.log", "Remove console.log before production"),
    (r"eval\(", "Avoid eval() - security risk"),
]

PYTHON_ISSUES = [
    (r"except:", "Bare except - specify exception type"),
    (r"import \*", "Wildcard import - import specific names"),
]


def review_code(task_id: str, path: str) -> dict:
    """Review a file for common code quality issues.

    Args:
        task_id: Task identifier.
        path: Relative path within task files directory.

    Returns:
        Dict with issues found, severity, and suggestions.
    """
    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    try:
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        content = file_path.read_text(encoding="utf-8")
        ext = file_path.suffix.lower()
        issues = []

        if ext in (".html", ".htm"):
            patterns = HTML_ISSUES
            issues.extend(_check_html_structure(content))
        elif ext == ".css":
            patterns = CSS_ISSUES
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            patterns = JS_ISSUES
        elif ext == ".py":
            patterns = PYTHON_ISSUES
        else:
            patterns = []

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    issues.append({
                        "line": i,
                        "message": message,
                        "severity": "warning",
                        "code": line.strip()[:80],
                    })

        if len(content) > 50000:
            issues.append({"line": 0, "message": "File >50KB - consider splitting", "severity": "info", "code": ""})

        return {
            "success": True,
            "path": path,
            "task_id": task_id,
            "issues": issues,
            "total_issues": len(issues),
            "lines": len(lines),
            "size": len(content),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_project_checks(task_id: str) -> dict:
    """Run project-level checks based on detected project type.

    Supports: HTML/CSS/JS, Python, Node/React projects.

    Args:
        task_id: Task identifier.

    Returns:
        Dict with check results.
    """
    files_dir = get_files_dir(task_id)
    if not files_dir.exists():
        return {"success": False, "error": "Task workspace not found"}

    results = []
    project_type = "unknown"

    # Detect project type
    has_package_json = (files_dir / "package.json").exists()
    has_index_html = (files_dir / "index.html").exists()
    has_py_files = any(files_dir.rglob("*.py"))

    if has_package_json:
        project_type = "node"
        results.append(_check_node_project(files_dir))
    if has_index_html:
        project_type = "html" if project_type == "unknown" else project_type
        results.append(_check_html_project(files_dir))
    if has_py_files:
        project_type = "python" if project_type == "unknown" else project_type
        results.append(_check_python_project(files_dir))

    # General checks
    results.append(_check_file_structure(files_dir))

    all_errors = []
    all_warnings = []
    for r in results:
        all_errors.extend(r.get("errors", []))
        all_warnings.extend(r.get("warnings", []))

    return {
        "success": True,
        "task_id": task_id,
        "project_type": project_type,
        "checks": results,
        "total_errors": len(all_errors),
        "total_warnings": len(all_warnings),
        "passed": len(all_errors) == 0,
    }


def detect_runtime_errors(task_id: str) -> dict:
    """Scan task workspace for common runtime error patterns."""
    files_dir = get_files_dir(task_id)
    if not files_dir.exists():
        return {"success": False, "error": "Task workspace not found"}

    errors = []
    try:
        for file_path in files_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in (".py", ".js", ".html", ".css"):
                continue

            rel_path = str(file_path.relative_to(files_dir)).replace("\\", "/")
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            if file_path.suffix.lower() in (".html", ".htm"):
                for match in re.finditer(r'(?:src|href)=["\']([^"\']+)["\']', content):
                    ref = match.group(1)
                    if ref.startswith(("http", "//", "#", "data:", "mailto:")):
                        continue
                    ref_path = file_path.parent / ref
                    if not ref_path.exists():
                        errors.append({"file": rel_path, "message": f"Broken reference: {ref}", "severity": "error"})

        return {"success": True, "task_id": task_id, "errors": errors, "total": len(errors)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def suggest_fixes(task_id: str, path: str) -> dict:
    """Suggest fixes for issues found in a file."""
    review = review_code(task_id, path)
    if not review.get("success"):
        return review

    fixes = []
    for issue in review.get("issues", []):
        fix = _generate_fix_suggestion(issue)
        if fix:
            fixes.append(fix)

    return {"success": True, "path": path, "task_id": task_id, "fixes": fixes, "total_fixes": len(fixes)}


def auto_fix(task_id: str, path: str) -> dict:
    """Automatically fix simple issues in a file.

    In Safe Mode: creates a pending file change with the fix.
    In Autonomous Mode: applies directly and records diff.

    Args:
        task_id: Task identifier.
        path: Relative path within task files directory.

    Returns:
        Dict with applied fixes.
    """
    import config
    from app.tools.diff_tools import preview_file_change, set_diff_task_id

    safe, file_path, reason = resolve_safe_path(task_id, path, "files")
    if not safe:
        return {"success": False, "error": reason}

    if not file_path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    content = file_path.read_text(encoding="utf-8")
    original = content
    ext = file_path.suffix.lower()
    applied_fixes = []

    if ext in (".js", ".jsx"):
        if "var " in content:
            content = re.sub(r"\bvar\b", "let", content)
            applied_fixes.append("Replaced 'var' with 'let'")
        new_content = re.sub(r"(?<!=)==(?!=)", "===", content)
        if new_content != content:
            content = new_content
            applied_fixes.append("Replaced '==' with '==='")

    elif ext in (".html", ".htm"):
        new_content = re.sub(r"(<img\b(?![^>]*\balt=)[^>]*)(>)", r'\1 alt=""\2', content)
        if new_content != content:
            content = new_content
            applied_fixes.append("Added missing alt attributes to img tags")

    if content == original:
        return {"success": True, "path": path, "task_id": task_id, "fixes_applied": [], "changed": False}

    # Apply via diff system
    set_diff_task_id(task_id)
    result = preview_file_change(path, content)

    # In autonomous mode or if preview succeeded, write to disk
    if config.EXECUTION_MODE != "safe":
        file_path.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "path": path,
        "task_id": task_id,
        "fixes_applied": applied_fixes,
        "total_fixes": len(applied_fixes),
        "changed": True,
        "change_id": result.get("change_id"),
        "status": result.get("status"),
    }


# --- Internal helpers ---

def _check_html_structure(content: str) -> list[dict]:
    issues = []
    if "<!DOCTYPE" not in content.upper():
        issues.append({"line": 1, "message": "Missing DOCTYPE declaration", "severity": "warning", "code": ""})
    if "<title>" not in content.lower():
        issues.append({"line": 0, "message": "Missing <title> tag", "severity": "warning", "code": ""})
    if "</html>" not in content.lower():
        issues.append({"line": 0, "message": "Missing closing </html> tag", "severity": "error", "code": ""})
    return issues


def _check_node_project(files_dir: Path) -> dict:
    """Check Node.js project."""
    errors = []
    warnings = []
    pkg = files_dir / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            if "name" not in data:
                warnings.append("package.json missing 'name'")
        except json.JSONDecodeError:
            errors.append("package.json is invalid JSON")
    return {"check": "node_project", "errors": errors, "warnings": warnings}


def _check_html_project(files_dir: Path) -> dict:
    """Check HTML project."""
    errors = []
    warnings = []
    index = files_dir / "index.html"
    if index.exists():
        content = index.read_text(encoding="utf-8")
        if "<!DOCTYPE" not in content.upper():
            warnings.append("index.html missing DOCTYPE")
        if "<title>" not in content.lower():
            warnings.append("index.html missing <title>")
    return {"check": "html_project", "errors": errors, "warnings": warnings}


def _check_python_project(files_dir: Path) -> dict:
    """Check Python project via compileall."""
    errors = []
    warnings = []
    try:
        result = subprocess.run(
            ["py", "-m", "compileall", str(files_dir), "-q"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            errors.append(f"Python compile errors: {result.stderr.strip()[:200]}")
    except Exception:
        warnings.append("Could not run Python compile check")
    return {"check": "python_project", "errors": errors, "warnings": warnings}


def _check_file_structure(files_dir: Path) -> dict:
    """General file structure checks."""
    warnings = []
    file_count = sum(1 for _ in files_dir.rglob("*") if _.is_file())
    if file_count == 0:
        warnings.append("No files in workspace")
    return {"check": "file_structure", "errors": [], "warnings": warnings, "file_count": file_count}


def _generate_fix_suggestion(issue: dict) -> Optional[dict]:
    msg = issue.get("message", "")
    if "var" in msg:
        return {"description": "Replace 'var' with 'let'", "auto_fixable": True}
    if "==" in msg:
        return {"description": "Replace '==' with '==='", "auto_fixable": True}
    if "alt" in msg:
        return {"description": "Add alt attribute to img tags", "auto_fixable": True}
    if "console.log" in msg:
        return {"description": "Remove console.log statements", "auto_fixable": False}
    return None
