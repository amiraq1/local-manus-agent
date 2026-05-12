"""Central Permission System - checks all operations before execution."""
import os
import re
from enum import Enum
from pathlib import Path
from typing import Optional

from app.security.audit_log import log_security_event


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


# Dangerous path patterns
BLOCKED_PATH_PATTERNS = [
    ".ssh", ".gnupg", ".env", ".git/config",
    "/etc/shadow", "/etc/passwd",
    "id_rsa", "id_ed25519", ".pem",
    "docker.sock",
]

# Dangerous command patterns (regex)
BLOCKED_COMMAND_PATTERNS = [
    r"rm\s+(-rf?|--recursive)\s+[/~]",
    r"sudo\b",
    r"chmod\s+777",
    r"mkfs\b",
    r"dd\s+if=",
    r">\s*/dev/",
    r"shutdown|reboot|poweroff",
    r"curl\s.*\|\s*(ba)?sh",
    r"wget\s.*\|\s*(ba)?sh",
    r"nc\s+-l",  # netcat listener
    r"python.*-c.*import\s+os",
    r"eval\s*\(",
]

# Commands that need approval even in autonomous mode
APPROVAL_REQUIRED_PATTERNS = [
    r"pip\s+install",
    r"npm\s+install\s+-g",
    r"pkg\s+install",
    r"apt(-get)?\s+install",
    r"brew\s+install",
    r"curl\s+",
    r"wget\s+",
    r"git\s+(push|remote)",
    r"ssh\s+",
    r"scp\s+",
]

# Allowed network hosts
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]


def check_file_operation(task_id: str, path: str, operation: str) -> tuple[Decision, str]:
    """Check if a file operation is allowed.

    Args:
        task_id: Task identifier.
        path: File path being accessed.
        operation: read, write, delete, list.

    Returns:
        Tuple of (decision, reason).
    """
    path_lower = path.lower().replace("\\", "/")

    # Block absolute paths
    if os.path.isabs(path):
        log_security_event(task_id, "file_access", "high", operation, path, "deny", "Absolute path blocked")
        return Decision.DENY, "Absolute paths are not allowed"

    # Block path traversal
    if ".." in path.replace("\\", "/").split("/"):
        log_security_event(task_id, "file_access", "high", operation, path, "deny", "Path traversal blocked")
        return Decision.DENY, "Path traversal (..) is not allowed"

    # Block sensitive patterns
    for pattern in BLOCKED_PATH_PATTERNS:
        if pattern.lower() in path_lower:
            log_security_event(task_id, "file_access", "high", operation, path, "deny", f"Sensitive path: {pattern}")
            return Decision.DENY, f"Access to sensitive path blocked: {pattern}"

    log_security_event(task_id, "file_access", "low", operation, path, "allow", "")
    return Decision.ALLOW, "OK"


def check_command(task_id: str, command: str) -> tuple[Decision, str]:
    """Check if a shell command is allowed.

    Args:
        task_id: Task identifier.
        command: Shell command string.

    Returns:
        Tuple of (decision, reason).
    """
    cmd_lower = command.lower().strip()

    # Check blocked patterns
    for pattern in BLOCKED_COMMAND_PATTERNS:
        if re.search(pattern, cmd_lower):
            log_security_event(task_id, "command", "critical", "execute", command, "deny", f"Blocked pattern: {pattern}")
            return Decision.DENY, f"Dangerous command blocked: matches '{pattern}'"

    # Check approval-required patterns
    for pattern in APPROVAL_REQUIRED_PATTERNS:
        if re.search(pattern, cmd_lower):
            log_security_event(task_id, "command", "medium", "execute", command, "require_approval", f"Needs approval: {pattern}")
            return Decision.REQUIRE_APPROVAL, f"Command requires approval: matches '{pattern}'"

    # Check for pipe to shell
    if re.search(r"\|\s*(ba)?sh", cmd_lower):
        log_security_event(task_id, "command", "critical", "execute", command, "deny", "Pipe to shell")
        return Decision.DENY, "Piping to shell is blocked"

    log_security_event(task_id, "command", "low", "execute", command, "allow", "")
    return Decision.ALLOW, "OK"


def check_network_access(url: str, task_id: str = "") -> tuple[Decision, str]:
    """Check if a network URL is allowed.

    Args:
        url: URL being accessed.
        task_id: Task identifier.

    Returns:
        Tuple of (decision, reason).
    """
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
    except Exception:
        return Decision.DENY, f"Invalid URL: {url}"

    if host in ALLOWED_HOSTS:
        return Decision.ALLOW, "OK"

    from config import BROWSER_ALLOW_EXTERNAL_URLS
    if BROWSER_ALLOW_EXTERNAL_URLS:
        log_security_event(task_id, "network", "medium", "access", url, "allow", "External allowed by config")
        return Decision.ALLOW, "OK"

    log_security_event(task_id, "network", "medium", "access", url, "deny", "External URL blocked")
    return Decision.DENY, f"External URL blocked: {host}"


def check_browser_action(action: str, url: str = "", task_id: str = "") -> tuple[Decision, str]:
    """Check if a browser action is allowed.

    Args:
        action: Browser action (navigate, screenshot, evaluate, etc).
        url: URL if applicable.
        task_id: Task identifier.

    Returns:
        Tuple of (decision, reason).
    """
    if action == "navigate" and url:
        return check_network_access(url, task_id)

    if action == "evaluate":
        # JS evaluation is allowed but logged
        log_security_event(task_id, "browser", "low", action, url, "allow", "JS evaluation")

    return Decision.ALLOW, "OK"
