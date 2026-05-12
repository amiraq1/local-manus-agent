"""Platform detection and adaptation module."""
from app.platform.detector import detect_platform, is_termux, get_platform_status

__all__ = ["detect_platform", "is_termux", "get_platform_status"]
