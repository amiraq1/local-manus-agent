"""Code Review Tools - reviews code quality, detects errors, suggests fixes."""
import subprocess
import re
from pathlib import Path
from typing import Optional

from config import WORKSPACE_DIR
from app.tools.safety import is_path_safe, sanitize_path


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
    (r"print\(", "Consider using logging instead of print"),
]


def review_code(path: str) -> dict:
    """Review a file for common code quality issues.

    Args:
        path: Relative path within workspace.

    Returns:
        Dict with issues found, severity, and suggestions.
    """
    safe, reason = is_path_safe(path)
    if not safe:
        return {"success": False, "error": reason}

    try:
        file_path = sanitize_path(path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        content = file_path.read_text(encoding="utf-8")
        ext = file_path.suffix.lower()
        issues = []

        # Select patterns based on file type
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

        # Run pattern checks
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

        # Check file size
        if len(content) > 50000:
            issues.append({
                "line": 0,
                "message": "File is very large (>50KB) - consider splitting",
                "severity": "info",
                "code": "",
            })

        return {
            "success": True,
            "path": path,
            "issues": issues,
            "total_issues": len(issues),
            "lines": len(lines),
            "size": len(content),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_lint(path: str) -> dict:
    """Run syntax/lint check on a file based on its type.

    Args:
        path: Relative path within workspace.

    Returns:
        Dict with lint results.
    """
    safe, reason = is_path_safe(path)
    if not safe:
        return {"success": False, "error": reason}

    try:
        file_path = sanitize_path(path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        ext = file_path.suffix.lower()
        errors = []

        if ext == ".py":
            errors = _lint_python(file_path)
        elif ext in (".html", ".htm"):
            errors = _lint_html(file_path)
        elif ext in (".js", ".jsx"):
            errors = _lint_js(file_path)
        elif ext == ".css":
            errors = _lint_css(file_path)
        else:
            return {"success": True, "path": path, "errors": [], "message": "No linter for this file type"}

        return {
            "success": True,
            "path": path,
            "errors": errors,
            "total_errors": len(errors),
            "has_errors": len(errors) > 0,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def detect_runtime_errors() -> dict:
    """Scan workspace for common runtime error patterns.

    Returns:
        Dict with detected potential runtime errors.
    """
    errors = []
    try:
        for file_path in WORKSPACE_DIR.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in (".py", ".js", ".html", ".css"):
                continue

            rel_path = str(file_path.relative_to(WORKSPACE_DIR)).replace("\\", "/")
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Check for broken references
            if file_path.suffix.lower() in (".html", ".htm"):
                # Check for broken CSS/JS links
                for match in re.finditer(r'(?:src|href)=["\']([^"\']+)["\']', content):
                    ref = match.group(1)
                    if ref.startswith(("http", "//", "#", "data:", "mailto:")):
                        continue
                    ref_path = file_path.parent / ref
                    if not ref_path.exists():
                        errors.append({
                            "file": rel_path,
                            "message": f"Broken reference: {ref}",
                            "severity": "error",
                        })

        return {"success": True, "errors": errors, "total": len(errors)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def suggest_fixes(path: str) -> dict:
    """Suggest fixes for issues found in a file.

    Args:
        path: Relative path within workspace.

    Returns:
        Dict with suggested fixes.
    """
    review = review_code(path)
    if not review.get("success"):
        return review

    fixes = []
    for issue in review.get("issues", []):
        fix = _generate_fix_suggestion(issue, path)
        if fix:
            fixes.append(fix)

    return {
        "success": True,
        "path": path,
        "fixes": fixes,
        "total_fixes": len(fixes),
    }


def auto_fix(path: str) -> dict:
    """Automatically fix simple issues in a file.

    Only fixes safe, non-breaking issues like:
    - var -> let/const
    - == -> ===
    - Missing alt attributes

    Args:
        path: Relative path within workspace.

    Returns:
        Dict with applied fixes and new content.
    """
    safe, reason = is_path_safe(path)
    if not safe:
        return {"success": False, "error": reason}

    try:
        file_path = sanitize_path(path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        content = file_path.read_text(encoding="utf-8")
        original = content
        ext = file_path.suffix.lower()
        applied_fixes = []

        if ext in (".js", ".jsx"):
            # Fix var -> let
            if "var " in content:
                content = re.sub(r"\bvar\b", "let", content)
                applied_fixes.append("Replaced 'var' with 'let'")

            # Fix == -> === (but not !== or ===)
            new_content = re.sub(r"(?<!=)==(?!=)", "===", content)
            if new_content != content:
                content = new_content
                applied_fixes.append("Replaced '==' with '==='")

        elif ext in (".html", ".htm"):
            # Add alt="" to img tags missing alt
            new_content = re.sub(
                r"(<img\b(?![^>]*\balt=)[^>]*)(>)",
                r'\1 alt=""\2',
                content,
            )
            if new_content != content:
                content = new_content
                applied_fixes.append("Added missing alt attributes to img tags")

        if content != original:
            file_path.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "path": path,
                "fixes_applied": applied_fixes,
                "total_fixes": len(applied_fixes),
                "changed": True,
            }
        else:
            return {
                "success": True,
                "path": path,
                "fixes_applied": [],
                "total_fixes": 0,
                "changed": False,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Internal helpers ---

def _check_html_structure(content: str) -> list[dict]:
    """Check HTML structural issues."""
    issues = []
    if "<!DOCTYPE" not in content.upper():
        issues.append({"line": 1, "message": "Missing DOCTYPE declaration", "severity": "warning", "code": ""})
    if "<title>" not in content.lower():
        issues.append({"line": 0, "message": "Missing <title> tag", "severity": "warning", "code": ""})
    if "</html>" not in content.lower():
        issues.append({"line": 0, "message": "Missing closing </html> tag", "severity": "error", "code": ""})
    return issues


def _lint_python(file_path: Path) -> list[dict]:
    """Lint Python file using py_compile."""
    try:
        result = subprocess.run(
            ["py", "-m", "py_compile", str(file_path)],
            capture_output=True, text=True, timeout=10,
            cwd=str(WORKSPACE_DIR),
        )
        if result.returncode != 0:
            return [{"message": result.stderr.strip(), "severity": "error"}]
        return []
    except Exception:
        return []


def _lint_html(file_path: Path) -> list[dict]:
    """Basic HTML lint - check for unclosed tags."""
    content = file_path.read_text(encoding="utf-8")
    errors = []
    # Simple check: count opening vs closing tags for common elements
    for tag in ["div", "span", "p", "ul", "ol", "li", "table", "tr", "td"]:
        opens = len(re.findall(f"<{tag}[\\s>]", content, re.IGNORECASE))
        closes = len(re.findall(f"</{tag}>", content, re.IGNORECASE))
        if opens != closes:
            errors.append({
                "message": f"Mismatched <{tag}> tags: {opens} opening, {closes} closing",
                "severity": "warning",
            })
    return errors


def _lint_js(file_path: Path) -> list[dict]:
    """Basic JS lint - check for syntax issues."""
    content = file_path.read_text(encoding="utf-8")
    errors = []
    # Check for unmatched braces
    if content.count("{") != content.count("}"):
        errors.append({"message": "Unmatched curly braces", "severity": "error"})
    if content.count("(") != content.count(")"):
        errors.append({"message": "Unmatched parentheses", "severity": "error"})
    if content.count("[") != content.count("]"):
        errors.append({"message": "Unmatched square brackets", "severity": "error"})
    return errors


def _lint_css(file_path: Path) -> list[dict]:
    """Basic CSS lint."""
    content = file_path.read_text(encoding="utf-8")
    errors = []
    if content.count("{") != content.count("}"):
        errors.append({"message": "Unmatched curly braces in CSS", "severity": "error"})
    return errors


def _generate_fix_suggestion(issue: dict, path: str) -> Optional[dict]:
    """Generate a fix suggestion for an issue."""
    msg = issue.get("message", "")
    if "var" in msg:
        return {"description": "Replace 'var' with 'let' or 'const'", "auto_fixable": True}
    if "==" in msg:
        return {"description": "Replace '==' with '==='", "auto_fixable": True}
    if "alt" in msg:
        return {"description": "Add alt attribute to img tags", "auto_fixable": True}
    if "console.log" in msg:
        return {"description": "Remove console.log statements", "auto_fixable": False}
    return None
