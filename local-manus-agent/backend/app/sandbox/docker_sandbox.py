"""Docker Sandbox implementation - runs commands in isolated containers."""
import subprocess
import shutil
import os
from pathlib import Path
from typing import Optional

from app.sandbox.base import SandboxBackend, SandboxResult
from app.sandbox.policies import build_container_args, validate_config, SandboxPolicyError
from config import (
    WORKSPACE_DIR,
    SANDBOX_IMAGE,
    SANDBOX_COMMAND_TIMEOUT,
)


class DockerSandbox(SandboxBackend):
    """Docker-based sandbox for isolated command execution.

    Each task gets its own container with:
    - Limited memory and CPU
    - No network (by default)
    - Non-root user
    - Only workspace directory mounted
    - No docker socket access
    """

    def __init__(self):
        self._containers: dict[str, str] = {}  # task_id -> container_name
        self._last_command: Optional[str] = None

    @property
    def last_command(self) -> Optional[str]:
        return self._last_command

    def _container_name(self, task_id: str) -> str:
        """Generate a container name for a task."""
        safe_id = task_id.replace("-", "")[:12]
        return f"manus-sandbox-{safe_id}"

    def _docker_available(self) -> bool:
        """Check if docker CLI is available."""
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _image_exists(self) -> bool:
        """Check if the sandbox image exists."""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", SANDBOX_IMAGE],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def create_container(self, task_id: str) -> dict:
        """Create and start a sandbox container for a task."""
        if not self._docker_available():
            return {"success": False, "error": "Docker is not available"}

        if not self._image_exists():
            return {"success": False, "error": f"Sandbox image not found: {SANDBOX_IMAGE}. Build it with: docker build -f backend/sandbox.Dockerfile -t {SANDBOX_IMAGE} backend"}

        valid, reason = validate_config()
        if not valid:
            return {"success": False, "error": f"Invalid sandbox config: {reason}"}

        container_name = self._container_name(task_id)

        # Remove existing container if any
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True, timeout=10,
        )

        # Build args
        workspace_path = str(WORKSPACE_DIR.resolve())
        try:
            args = build_container_args(container_name, workspace_path)
        except SandboxPolicyError as e:
            return {"success": False, "error": str(e)}

        # Create container (detached, with sleep to keep alive)
        cmd = ["docker", "run", "-d"] + args + [SANDBOX_IMAGE, "sleep", "3600"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {"success": False, "error": f"Failed to create container: {result.stderr.strip()}"}

            container_id = result.stdout.strip()[:12]
            self._containers[task_id] = container_name
            return {
                "success": True,
                "container_name": container_name,
                "container_id": container_id,
                "task_id": task_id,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Container creation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_command(self, task_id: str, command: str, cwd: str = "/workspace") -> SandboxResult:
        """Run a command inside the sandbox container."""
        container_name = self._containers.get(task_id)
        if not container_name:
            # Auto-create container
            create_result = self.create_container(task_id)
            if not create_result.get("success"):
                return SandboxResult(
                    success=False,
                    error=create_result.get("error", "Failed to create container"),
                )
            container_name = self._containers[task_id]

        self._last_command = command

        # Execute command in container
        exec_cmd = [
            "docker", "exec",
            "-w", cwd,
            container_name,
            "sh", "-c", command,
        ]

        try:
            result = subprocess.run(
                exec_cmd,
                capture_output=True,
                text=True,
                timeout=SANDBOX_COMMAND_TIMEOUT,
            )
            return SandboxResult(
                success=result.returncode == 0,
                stdout=result.stdout[:5000],
                stderr=result.stderr[:2000],
                returncode=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                error=f"Command timed out ({SANDBOX_COMMAND_TIMEOUT}s limit)",
                timed_out=True,
            )
        except Exception as e:
            return SandboxResult(success=False, error=str(e))

    def copy_workspace_to_container(self, task_id: str) -> dict:
        """Copy workspace files into the container."""
        container_name = self._containers.get(task_id)
        if not container_name:
            return {"success": False, "error": "No container for this task"}

        try:
            # docker cp workspace/. container:/workspace/
            src = str(WORKSPACE_DIR) + "/."
            result = subprocess.run(
                ["docker", "cp", src, f"{container_name}:/workspace/"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy_workspace_from_container(self, task_id: str) -> dict:
        """Copy files from container back to workspace."""
        container_name = self._containers.get(task_id)
        if not container_name:
            return {"success": False, "error": "No container for this task"}

        try:
            # docker cp container:/workspace/. workspace/
            dest = str(WORKSPACE_DIR)
            result = subprocess.run(
                ["docker", "cp", f"{container_name}:/workspace/.", dest],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_container(self, task_id: str) -> dict:
        """Stop a running container."""
        container_name = self._containers.get(task_id)
        if not container_name:
            return {"success": True, "message": "No container for this task"}

        try:
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True, text=True, timeout=15,
            )
            return {"success": result.returncode == 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_container(self, task_id: str) -> dict:
        """Remove a container."""
        container_name = self._containers.get(task_id)
        if not container_name:
            return {"success": True, "message": "No container for this task"}

        try:
            result = subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                self._containers.pop(task_id, None)
            return {"success": result.returncode == 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_container_status(self, task_id: str) -> dict:
        """Get the status of a container."""
        container_name = self._containers.get(task_id)
        if not container_name:
            return {"status": "none", "task_id": task_id, "exists": False}

        try:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", container_name],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                status = result.stdout.strip()
                return {
                    "status": status,
                    "task_id": task_id,
                    "container_name": container_name,
                    "exists": True,
                }
            return {"status": "not_found", "task_id": task_id, "exists": False}
        except Exception as e:
            return {"status": "error", "error": str(e), "task_id": task_id, "exists": False}

    def reset(self) -> dict:
        """Stop and remove all sandbox containers."""
        removed = []
        for task_id in list(self._containers.keys()):
            self.remove_container(task_id)
            removed.append(task_id)
        return {"success": True, "removed": removed}

    def get_global_status(self) -> dict:
        """Get overall sandbox status."""
        docker_ok = self._docker_available()
        image_ok = self._image_exists() if docker_ok else False

        return {
            "enabled": True,
            "docker_available": docker_ok,
            "image_available": image_ok,
            "image": SANDBOX_IMAGE,
            "network_enabled": __import__("config").SANDBOX_NETWORK_ENABLED,
            "memory_limit": __import__("config").SANDBOX_MEMORY_LIMIT,
            "cpu_limit": __import__("config").SANDBOX_CPU_LIMIT,
            "timeout": SANDBOX_COMMAND_TIMEOUT,
            "active_containers": len(self._containers),
            "containers": {tid: name for tid, name in self._containers.items()},
            "last_command": self._last_command,
        }


# Singleton instance
_sandbox: Optional[DockerSandbox] = None


def get_docker_sandbox() -> DockerSandbox:
    """Get the global DockerSandbox instance."""
    global _sandbox
    if _sandbox is None:
        _sandbox = DockerSandbox()
    return _sandbox
