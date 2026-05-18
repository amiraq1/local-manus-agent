"""Configuration for Local Manus Agent backend."""
import os
from pathlib import Path

APP_VERSION = "1.2.0"

# Base paths
BASE_DIR = Path(__file__).parent
WORKSPACE_DIR = BASE_DIR / "workspace"

# Ensure workspace exists
WORKSPACE_DIR.mkdir(exist_ok=True)

# LLM Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")  # Options: "ollama", "litert"

OLLAMA_CONFIG = {
    "base_url": os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    "model": os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b"),
    "temperature": 0.7,
    "max_tokens": 4096,
}

LITERT_CONFIG = {
    "model_path": "",
    "temperature": 0.7,
    "max_tokens": 4096,
    "device": "cpu",
    "enable_streaming": True,
    "fallback_provider": "ollama",
    "allow_fallback": True,
}

# Preview server
PREVIEW_PORT = 3001
PREVIEW_HOST = "localhost"

# Safety settings
BLOCKED_COMMANDS = [
    "rm -rf /",
    "sudo",
    "chmod 777 /",
    "curl | bash",
    "wget",
    "mkfs",
    "dd if=",
    "> /dev/",
    "shutdown",
    "reboot",
    "format",
]

BLOCKED_PATH_PATTERNS = [
    ".ssh",
    ".env",
    "/etc/",
    "/var/",
    "/usr/",
    "C:\\Windows",
    "C:\\Program Files",
]

# Agent settings
MAX_STEPS = 20
MAX_RETRIES = 3

# Execution mode: "safe" or "autonomous"
# safe: requires user approval for shell commands
# autonomous: executes all commands without approval
EXECUTION_MODE = "safe"

# Whether to allow commands without approval in autonomous mode
ALLOW_AUTONOMOUS_COMMANDS = False

# Browser Automation settings
BROWSER_ALLOW_EXTERNAL_URLS = False  # Only localhost by default
BROWSER_HEADLESS = True
BROWSER_TIMEOUT = 15000  # ms

# HTTP/API exposure settings
ALLOW_REMOTE_ACCESS = os.environ.get("ALLOW_REMOTE_ACCESS", "false").lower() in ("1", "true", "yes")
API_TOKEN = os.environ.get("LOCAL_MANUS_API_TOKEN", "")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]

# Docker Sandbox settings
SANDBOX_ENABLED = True
SANDBOX_BACKEND = "docker"
SANDBOX_IMAGE = "local-manus-sandbox:latest"
SANDBOX_MEMORY_LIMIT = "512m"
SANDBOX_CPU_LIMIT = 1
SANDBOX_COMMAND_TIMEOUT = 30
SANDBOX_NETWORK_ENABLED = False

# Platform settings
PLATFORM_MODE = "auto"  # auto, desktop, termux
TERMUX_MODE = False
TERMUX_DISABLE_DOCKER = True
TERMUX_BROWSER_MODE = "disabled"  # disabled, chromium
TERMUX_CHROMIUM_PATH = ""
TERMUX_HOST = "127.0.0.1"

# LLM Presets
LLM_PRESETS = {
    "ollama": {
        "name": "Ollama (qwen2.5-coder:7b)",
        "provider": "ollama",
        "description": "Local Ollama instance with qwen2.5-coder:7b",
    },
    "gemma-e2b-litert": {
        "name": "Gemma E2B LiteRT-LM",
        "provider": "litert",
        "model_path": "",  # Set via GEMMA_E2B_LITERT_MODEL_PATH or auto-detect
        "description": "Google Gemma 3n E2B int4 via LiteRT-LM",
        "download_instructions": (
            "Download from Hugging Face:\n"
            "  huggingface-cli login\n"
            "  huggingface-cli download google/gemma-3n-E2B-it-litert-lm "
            "gemma-3n-E2B-it-int4.litertlm --local-dir models/gemma-e2b"
        ),
    },
    "litert-custom": {
        "name": "LiteRT-LM (Custom Path)",
        "provider": "litert",
        "model_path": "",
        "description": "Custom LiteRT-LM model from LITERT_CONFIG.model_path",
    },
}

# Gemma E2B specific path (set this to your downloaded model)
GEMMA_E2B_LITERT_MODEL_PATH = ""

# Active preset
ACTIVE_LLM_PRESET = "ollama"
