"""Configuration for Local Manus Agent backend."""
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
WORKSPACE_DIR = BASE_DIR / "workspace"

# Ensure workspace exists
WORKSPACE_DIR.mkdir(exist_ok=True)

# LLM Configuration
LLM_PROVIDER = "ollama"  # Options: "ollama", "litert"

OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "qwen2.5-coder:7b",
    "temperature": 0.7,
    "max_tokens": 4096,
}

LITERT_CONFIG = {
    "model_path": "",
    "temperature": 0.7,
    "max_tokens": 4096,
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

# Docker Sandbox settings
SANDBOX_ENABLED = True
SANDBOX_BACKEND = "docker"
SANDBOX_IMAGE = "local-manus-sandbox:latest"
SANDBOX_MEMORY_LIMIT = "512m"
SANDBOX_CPU_LIMIT = 1
SANDBOX_COMMAND_TIMEOUT = 30
SANDBOX_NETWORK_ENABLED = False

# Docker Sandbox settings
SANDBOX_ENABLED = True
SANDBOX_BACKEND = "docker"  # Only "docker" supported currently
SANDBOX_IMAGE = "local-manus-sandbox:latest"
SANDBOX_MEMORY_LIMIT = "512m"
SANDBOX_CPU_LIMIT = 1
SANDBOX_COMMAND_TIMEOUT = 30  # seconds
SANDBOX_NETWORK_ENABLED = False  # No network by default
