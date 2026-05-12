"""Base interface for sandbox backends."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SandboxResult:
    """Result of a command executed in a sandbox."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    error: Optional[str] = None
    timed_out: bool = False

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "error": self.error,
            "timed_out": self.timed_out,
        }


class SandboxBackend(ABC):
    """Abstract base class for sandbox backends."""

    @abstractmethod
    def create_container(self, task_id: str) -> dict:
        """Create a new sandbox container for a task."""
        ...

    @abstractmethod
    def run_command(self, task_id: str, command: str, cwd: str = "/workspace") -> SandboxResult:
        """Run a command inside the sandbox."""
        ...

    @abstractmethod
    def copy_workspace_to_container(self, task_id: str) -> dict:
        """Copy workspace files into the container."""
        ...

    @abstractmethod
    def copy_workspace_from_container(self, task_id: str) -> dict:
        """Copy files from container back to workspace."""
        ...

    @abstractmethod
    def stop_container(self, task_id: str) -> dict:
        """Stop a running container."""
        ...

    @abstractmethod
    def remove_container(self, task_id: str) -> dict:
        """Remove a container."""
        ...

    @abstractmethod
    def get_container_status(self, task_id: str) -> dict:
        """Get the status of a container."""
        ...
