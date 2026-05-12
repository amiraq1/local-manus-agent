"""Security policies for Docker sandbox execution."""
from config import (
    SANDBOX_IMAGE,
    SANDBOX_MEMORY_LIMIT,
    SANDBOX_CPU_LIMIT,
    SANDBOX_COMMAND_TIMEOUT,
    SANDBOX_NETWORK_ENABLED,
)

# Absolutely forbidden mount paths
FORBIDDEN_MOUNTS = [
    "/var/run/docker.sock",
    "/var/run/docker",
    "/var/lib/docker",
    "/etc/shadow",
    "/etc/passwd",
    "/root",
    "/proc",
    "/sys",
    "/dev",
    "C:\\Windows",
    "C:\\Program Files",
]

# Forbidden docker flags
FORBIDDEN_FLAGS = [
    "--privileged",
    "--cap-add=ALL",
    "--cap-add=SYS_ADMIN",
    "--pid=host",
    "--net=host",
    "--network=host",
    "--ipc=host",
]


class SandboxPolicyError(Exception):
    """Raised when a sandbox operation violates security policy."""
    pass


def validate_config() -> tuple[bool, str]:
    """Validate sandbox configuration."""
    if not SANDBOX_IMAGE:
        return False, "SANDBOX_IMAGE not configured"
    if not SANDBOX_MEMORY_LIMIT:
        return False, "SANDBOX_MEMORY_LIMIT not configured"
    try:
        cpu = float(SANDBOX_CPU_LIMIT)
        if cpu <= 0 or cpu > 8:
            return False, f"SANDBOX_CPU_LIMIT must be 0-8, got {cpu}"
    except (ValueError, TypeError):
        return False, f"SANDBOX_CPU_LIMIT invalid: {SANDBOX_CPU_LIMIT}"
    if SANDBOX_COMMAND_TIMEOUT <= 0:
        return False, "SANDBOX_COMMAND_TIMEOUT must be positive"
    return True, "OK"


def validate_mount_path(host_path: str) -> tuple[bool, str]:
    """Check that a host path is safe to mount."""
    path_normalized = host_path.replace("\\", "/").lower()
    for forbidden in FORBIDDEN_MOUNTS:
        if forbidden.lower() in path_normalized:
            return False, f"Forbidden mount path: {forbidden}"
    if "docker.sock" in path_normalized:
        return False, "Docker socket mount is strictly forbidden"
    return True, "OK"


def build_container_args(container_name: str, workspace_host_path: str) -> list[str]:
    """Build secure docker run arguments.

    Args:
        container_name: Name for the container.
        workspace_host_path: Host path to mount as /workspace.

    Returns:
        List of docker CLI arguments.

    Raises:
        SandboxPolicyError: If security constraints are violated.
    """
    safe, reason = validate_mount_path(workspace_host_path)
    if not safe:
        raise SandboxPolicyError(reason)

    # Normalize path for docker
    host_path = workspace_host_path.replace("\\", "/")

    args = [
        "--name", container_name,
        # Resource limits
        "--memory", SANDBOX_MEMORY_LIMIT,
        "--memory-swap", SANDBOX_MEMORY_LIMIT,
        "--cpus", str(SANDBOX_CPU_LIMIT),
        "--pids-limit", "256",
        # Security: drop all capabilities
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        # Non-root user (UID 1000 from sandbox Dockerfile)
        "--user", "1000:1000",
        # Network control
        "--network", "bridge" if SANDBOX_NETWORK_ENABLED else "none",
        # Workspace mount
        "-v", f"{host_path}:/workspace:rw",
        "-w", "/workspace",
    ]

    # Final validation
    joined = " ".join(args).lower()
    for forbidden in FORBIDDEN_FLAGS:
        if forbidden.lower() in joined:
            raise SandboxPolicyError(f"Forbidden flag: {forbidden}")
    if "docker.sock" in joined:
        raise SandboxPolicyError("Docker socket mount detected")

    return args
