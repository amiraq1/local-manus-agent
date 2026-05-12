"""LiteRT-LM CLI Provider - uses the litert-lm.exe binary to run .litertlm models.

This provider runs the local CLI as a subprocess, which avoids needing a Python SDK.
Works on Windows/Linux/macOS wherever the CLI is installed.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import AsyncGenerator, Optional

from app.llm.base import LocalLLMProvider
from config import LITERT_CONFIG


# Default CLI search paths (Windows-friendly)
_DEFAULT_CLI_PATHS = [
    r"C:\Users\Aledari\.local\bin\litert-lm.exe",
    r"C:\Program Files\litert-lm\litert-lm.exe",
    "/usr/local/bin/litert-lm",
    "/usr/bin/litert-lm",
]


def find_cli(explicit_path: str = "") -> Optional[str]:
    """Find the litert-lm CLI executable.

    Order:
    1. Explicit path from config/settings
    2. shutil.which("litert-lm")
    3. Default well-known paths
    """
    if explicit_path and Path(explicit_path).is_file():
        return explicit_path

    found = shutil.which("litert-lm") or shutil.which("litert-lm.exe")
    if found:
        return found

    for p in _DEFAULT_CLI_PATHS:
        if Path(p).is_file():
            return p

    # Check user home on Windows
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if home:
        candidate = Path(home) / ".local" / "bin" / ("litert-lm.exe" if os.name == "nt" else "litert-lm")
        if candidate.is_file():
            return str(candidate)

    return None


def get_cli_version(cli_path: str) -> str:
    """Get CLI version string."""
    try:
        r = subprocess.run([cli_path, "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return (r.stdout or r.stderr).strip().split("\n")[0]
    except Exception:
        pass
    return "unknown"


class LiteRTCLIProvider(LocalLLMProvider):
    """LiteRT-LM provider that uses the CLI subprocess."""

    def __init__(self):
        self.model_path = LITERT_CONFIG.get("model_path", "")
        self.temperature = LITERT_CONFIG.get("temperature", 0.7)
        self.max_tokens = LITERT_CONFIG.get("max_tokens", 4096)
        self.backend = LITERT_CONFIG.get("backend", "cpu")
        self.cli_path = LITERT_CONFIG.get("cli_path", "")
        self.timeout = int(LITERT_CONFIG.get("timeout", 180))

        # Pull from user_config if available
        try:
            from app.user_config_manager import load_user_config
            cfg = load_user_config()
            llm_cfg = cfg.get("llm", {})
            self.cli_path = self.cli_path or llm_cfg.get("litert_cli_path", "")
            self.backend = llm_cfg.get("litert_backend", self.backend)
            self.timeout = int(llm_cfg.get("litert_timeout", self.timeout))
            # Also try user-set model path
            if not self.model_path:
                mp = cfg.get("model_paths", {}).get("gemma-e2b-litert", "")
                if mp:
                    self.model_path = mp
        except Exception:
            pass

        # Resolve CLI
        self._resolved_cli = find_cli(self.cli_path)

    def is_available(self) -> bool:
        """True if CLI and model both exist."""
        if not self._resolved_cli:
            return False
        if not self.model_path or not Path(self.model_path).exists():
            return False
        return True

    def model_info(self) -> dict:
        """Return provider status."""
        cli_exists = bool(self._resolved_cli)
        model_exists = bool(self.model_path and Path(self.model_path).exists())

        info = {
            "provider": "litert_cli",
            "runtime": "cli",
            "cli_path": self._resolved_cli or "",
            "cli_available": cli_exists,
            "model_path": self.model_path,
            "model_exists": model_exists,
            "backend": self.backend,
            "timeout": self.timeout,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "available": self.is_available(),
        }

        if cli_exists:
            info["cli_version"] = get_cli_version(self._resolved_cli)

        if cli_exists and model_exists:
            info["status_code"] = "ready_cli"
        elif cli_exists and not model_exists:
            info["status_code"] = "cli_ready_model_missing"
            info["error"] = f"CLI found at {self._resolved_cli}, but model file missing"
        elif not cli_exists and model_exists:
            info["status_code"] = "model_ready_cli_missing"
            info["error"] = "Model file found, but litert-lm CLI not installed"
        else:
            info["status_code"] = "not_configured"
            info["error"] = "Neither CLI nor model available"

        return info

    def _messages_to_prompt(self, messages) -> str:
        """Convert messages (string or list) to a single prompt."""
        if isinstance(messages, str):
            return messages
        if isinstance(messages, list):
            parts = []
            for m in messages:
                if isinstance(m, dict):
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    parts.append(f"{role}: {content}")
                else:
                    parts.append(str(m))
            return "\n".join(parts)
        return str(messages)

    def _run_cli(self, prompt: str) -> dict:
        """Run the CLI and return stdout/stderr/returncode."""
        if not self._resolved_cli:
            return {"success": False, "error": "CLI not found", "output": "", "stderr": ""}
        if not self.model_path or not Path(self.model_path).exists():
            return {"success": False, "error": "Model file not found", "output": "", "stderr": ""}

        cmd = [
            self._resolved_cli,
            "run",
            self.model_path,
            f"--backend={self.backend}",
            "--prompt",
            prompt,
        ]

        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8",
                errors="replace",
            )
            output = (r.stdout or "").strip()
            stderr = (r.stderr or "").strip()
            return {
                "success": r.returncode == 0,
                "output": output,
                "stderr": stderr,
                "returncode": r.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {self.timeout}s", "output": "", "stderr": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": "", "stderr": ""}

    async def generate(self, prompt, **kwargs) -> str:
        """Generate a response via the CLI."""
        prompt_text = self._messages_to_prompt(prompt)
        result = self._run_cli(prompt_text)
        if result["success"]:
            return result["output"]
        raise RuntimeError(result.get("error") or result.get("stderr") or "CLI run failed")

    async def stream(self, prompt, **kwargs) -> AsyncGenerator[str, None]:
        """Stream - currently yields the full output as one chunk."""
        text = await self.generate(prompt, **kwargs)
        if text:
            yield text

    def tool_call_parse(self, response: str) -> dict | None:
        """Parse a tool call JSON from response."""
        try:
            text = response.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
                if "tool" in parsed and "params" in parsed:
                    return parsed
        except (json.JSONDecodeError, KeyError):
            pass
        return None
