"""Termux-specific adaptations.

When running on Termux:
- Docker Sandbox is disabled
- Browser Automation is disabled by default
- Safe Mode is enforced
- Additional command restrictions apply
"""
import logging

logger = logging.getLogger(__name__)

# Extra blocked commands for Termux (package management needs approval)
TERMUX_EXTRA_BLOCKED = [
    "pkg install",
    "apt install",
    "apt-get install",
    "pip install",
    "npm install -g",
    "chmod 777",
    "rm -rf /",
    "rm -rf ~",
    "rm -rf $HOME",
    "rm -rf $PREFIX",
]


def apply_termux_config():
    """Apply Termux-specific configuration overrides.

    Called at startup when Termux is detected.
    """
    import config

    logger.info("Termux detected - applying platform adaptations")

    # Disable Docker
    config.SANDBOX_ENABLED = False

    # Disable browser automation
    config.BROWSER_ALLOW_EXTERNAL_URLS = False

    # Force safe mode
    config.EXECUTION_MODE = "safe"
    config.ALLOW_AUTONOMOUS_COMMANDS = False

    # Add extra blocked commands
    for cmd in TERMUX_EXTRA_BLOCKED:
        if cmd not in config.BLOCKED_COMMANDS:
            config.BLOCKED_COMMANDS.append(cmd)

    # Set host to localhost
    config.PREVIEW_HOST = "127.0.0.1"

    logger.info("Termux config applied: sandbox=off, browser=off, mode=safe")


def get_termux_info() -> dict:
    """Get Termux-specific environment info."""
    import os
    return {
        "prefix": os.environ.get("PREFIX", ""),
        "home": os.environ.get("HOME", ""),
        "termux_version": os.environ.get("TERMUX_VERSION", "unknown"),
        "android_data": os.environ.get("ANDROID_DATA", ""),
    }
