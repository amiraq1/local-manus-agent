"""Security Policies - platform-specific and mode-specific rules."""
from app.platform.detector import is_termux


def get_active_policies() -> dict:
    """Get the currently active security policies."""
    import config

    policies = {
        "mode": config.EXECUTION_MODE,
        "sandbox_enabled": config.SANDBOX_ENABLED,
        "browser_external_urls": config.BROWSER_ALLOW_EXTERNAL_URLS,
        "is_termux": is_termux(),
        "rules": [],
    }

    # Base rules (always active)
    policies["rules"].extend([
        "Path traversal (..) blocked",
        "Absolute paths blocked",
        "Sensitive files (.env, .ssh, keys) blocked",
        "Docker socket mount forbidden",
        "Dangerous commands (rm -rf /, sudo, etc) blocked",
        "Shell injection patterns blocked",
    ])

    # Safe mode rules
    if config.EXECUTION_MODE == "safe":
        policies["rules"].extend([
            "Shell commands require user approval",
            "Package installs require approval",
            "Network commands require approval",
        ])

    # Termux rules
    if is_termux():
        policies["rules"].extend([
            "Safe Mode enforced (cannot switch to autonomous)",
            "Docker Sandbox disabled",
            "Browser automation disabled by default",
            "Package management commands require approval",
        ])

    # Sandbox rules
    if config.SANDBOX_ENABLED:
        policies["rules"].extend([
            "Commands run in isolated Docker container",
            "No privileged mode",
            "No host network",
            "Memory/CPU limited",
            "Non-root user in container",
        ])

    return policies
