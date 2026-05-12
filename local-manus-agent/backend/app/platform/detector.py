"""Platform detection - identifies Termux, Desktop, or other environments."""
import os
import sys
import shutil
import subprocess
from typing import Optional


def is_termux() -> bool:
    """Detect if running inside Termux on Android."""
    prefix = os.environ.get("PREFIX", "")
    if "/data/data/com.termux" in prefix:
        return True
    if os.environ.get("TERMUX_VERSION"):
        return True
    if os.path.exists("/data/data/com.termux/files/usr"):
        return True
    return False


def detect_platform() -> str:
    """Detect the current platform mode.

    Returns:
        'termux', 'desktop', or 'unknown'
    """
    from config import PLATFORM_MODE

    if PLATFORM_MODE == "termux":
        return "termux"
    elif PLATFORM_MODE == "desktop":
        return "desktop"
    elif PLATFORM_MODE == "auto":
        if is_termux():
            return "termux"
        return "desktop"
    return "desktop"


def _cmd_available(cmd: str) -> bool:
    """Check if a command is available."""
    return shutil.which(cmd) is not None


def _cmd_version(cmd: str, args: list[str] = None) -> Optional[str]:
    """Get version string from a command."""
    try:
        a = args or ["--version"]
        r = subprocess.run([cmd] + a, capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return None


def get_platform_status() -> dict:
    """Get comprehensive platform status."""
    platform = detect_platform()
    termux = is_termux()

    limitations = []
    if termux:
        limitations = [
            "Docker Sandbox disabled (not available on Android)",
            "Browser Automation disabled by default",
            "Large LLM models may not fit in memory",
            "Performance depends on device hardware",
            "Use Ollama remote for better LLM performance",
        ]

    return {
        "platform_mode": platform,
        "is_termux": termux,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "node_available": _cmd_available("node"),
        "npm_available": _cmd_available("npm") or _cmd_available("npm.cmd"),
        "git_available": _cmd_available("git"),
        "docker_available": _cmd_available("docker") and not termux,
        "ollama_available": _cmd_available("ollama"),
        "browser_mode": "disabled" if termux else "playwright",
        "limitations": limitations,
        "os": sys.platform,
        "arch": os.uname().machine if hasattr(os, "uname") else "unknown",
    }
